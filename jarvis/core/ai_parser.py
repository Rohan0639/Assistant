"""
core/ai_parser.py

Phase 3 -- AI-powered intent and entity extraction via Groq.

Uses Groq (llama-3.3-70b-versatile) for all command parsing -- fast and free.

What's new vs the original:
    - Injects the user's personal style profile into the system prompt
      (the style profile is extracted separately by Gemini via style_learner.py)
    - Includes recent chat context (last 5 messages) so the LLM can
      resolve follow-up and ambiguous commands

Fallback:
    If Groq is unavailable or parsing fails, returns (INTENT_UNKNOWN, {})
    and the pipeline falls back to the Phase 2 rule-based system.

Model:
    llama-3.3-70b-versatile via Groq API (fast, free-tier eligible).
"""

import os
import json
import logging

from dotenv import load_dotenv
from groq import Groq

from jarvis.core.command import (
    INTENT_PLAY_MEDIA,
    INTENT_OPEN_APP,
    INTENT_OPEN_WEBSITE,
    INTENT_SEARCH_WEB,
    INTENT_WORKFLOW,
    INTENT_REMEMBER,
    INTENT_RECALL,
    INTENT_SYSTEM_CONTROL,
    INTENT_FILE_ACTION,
    INTENT_SYSTEM_INFO,
    INTENT_RUN_COMMAND,
    INTENT_UNKNOWN,
)

load_dotenv()
logger = logging.getLogger(__name__)

_VALID_INTENTS = {
    INTENT_PLAY_MEDIA, INTENT_OPEN_APP, INTENT_OPEN_WEBSITE,
    INTENT_SEARCH_WEB, INTENT_WORKFLOW, INTENT_REMEMBER,
    INTENT_RECALL, INTENT_SYSTEM_CONTROL, INTENT_FILE_ACTION,
    INTENT_SYSTEM_INFO, INTENT_RUN_COMMAND, INTENT_UNKNOWN,
}

# ── Base system prompt ────────────────────────────────────────────────────────

_BASE_SYSTEM_PROMPT = """
You are an intent classification engine for a personal desktop assistant.

Your job: analyze the user's input and return ONLY a JSON object with:
  - "intent": one of PLAY_MEDIA, OPEN_APP, OPEN_WEBSITE, SEARCH_WEB, WORKFLOW, REMEMBER, RECALL, SYSTEM_CONTROL, FILE_ACTION, SYSTEM_INFO, RUN_COMMAND, UNKNOWN
  - "entities": a dict with the relevant extracted value
  - "confidence": "high", "medium", or "low"

Intent definitions:
  PLAY_MEDIA      -- user wants to play music/audio. Entity key: "song_name"
  OPEN_APP        -- user wants to open a desktop application. Entity key: "app_name"
  OPEN_WEBSITE    -- user wants to navigate to a specific website. Entity key: "website"
  SEARCH_WEB      -- user wants to search the web for information. Entity key: "query"
  WORKFLOW        -- user wants to trigger a multi-step preset routine. Entity key: "workflow_name"
  REMEMBER        -- user wants to save a preference or fact. Entity keys: "key", "value"
  RECALL          -- user wants to retrieve a saved fact. Entity key: "key"
                     Use key="all" if user wants everything recalled.
  SYSTEM_CONTROL  -- user wants to control OS settings. Entity keys: "action", optional "value"
                     action values: volume_up, volume_down, mute, unmute, set_volume, sleep, shutdown, restart, lock
                     value: used for set_volume (e.g. "60" for 60%)
  FILE_ACTION     -- user wants to open a folder or file. Entity keys: "action", "target"
                     action values: open_folder, open_file
                     target: folder name (downloads, desktop, documents, etc.) or file path
  SYSTEM_INFO     -- user wants system information. Entity key: "metric"
                     metric values: battery, ram, cpu, disk, all
  RUN_COMMAND     -- user wants to run a named system command. Entity key: "command_name"
                     Examples: "ipconfig", "task manager", "disk cleanup", "ping google"
  UNKNOWN         -- none of the above applies

Workflow triggers (WORKFLOW intent):
  Phrases like "start coding session", "morning routine", "chill mode",
  "study session", "dev mode", "start my day", "relax", "entertainment mode",
  "prepare me to work", "focus mode", "start working" should return WORKFLOW.
  Extract the workflow name from the phrase as naturally as possible.
  Examples:
    "start my coding session"  -> WORKFLOW, workflow_name="coding session"
    "i want to chill"          -> WORKFLOW, workflow_name="chill mode"
    "morning routine please"   -> WORKFLOW, workflow_name="morning routine"

REMEMBER intent rules:
  User is telling you something to save. Extract key and value.
  Examples:
    "my name is Rohan"              -> REMEMBER, key="name", value="Rohan"
    "my favorite song is kesariya" -> REMEMBER, key="favorite_song", value="kesariya"
    "remember that I like chrome"  -> REMEMBER, key="favorite_app", value="chrome"
    "save github as my work site"  -> REMEMBER, key="favorite_website", value="github"
    "call me boss"                 -> REMEMBER, key="name", value="boss"

RECALL intent rules:
  User wants to retrieve stored information.
  Examples:
    "what's my name?"              -> RECALL, key="name"
    "what's my favorite song?"     -> RECALL, key="favorite_song"
    "what do you know about me?"   -> RECALL, key="all"
    "what have you remembered?"    -> RECALL, key="all"

Single-action intent rules:
  1. Return ONLY valid JSON. No explanation. No markdown. No code blocks.
  2. For PLAY_MEDIA: extract the song/artist name. If vague, make a reasonable interpretation.
  3. For OPEN_APP: extract just the app name.
  4. For OPEN_WEBSITE: extract just the site name or URL.
  5. For SEARCH_WEB: extract the full search query.
  6. If the user expresses a mood or feeling, infer the most logical action.
     Examples:
       "I'm bored"          -> PLAY_MEDIA, song_name="upbeat music"
       "I feel stressed"    -> PLAY_MEDIA, song_name="calming music"
       "I need to code"     -> OPEN_APP, app_name="vs code"
  7. The user may type casually, in mixed language (Hindi-English), with
     abbreviations or slang. Understand intent regardless of grammar.

SYSTEM_CONTROL examples:
  "volume up"               -> SYSTEM_CONTROL, action="volume_up"
  "turn down the volume"    -> SYSTEM_CONTROL, action="volume_down"
  "mute" / "silence"        -> SYSTEM_CONTROL, action="mute"
  "set volume to 60"        -> SYSTEM_CONTROL, action="set_volume", value="60"
  "sleep" / "suspend"       -> SYSTEM_CONTROL, action="sleep"
  "shutdown" / "turn off"   -> SYSTEM_CONTROL, action="shutdown"
  "restart" / "reboot"      -> SYSTEM_CONTROL, action="restart"
  "lock" / "lock screen"    -> SYSTEM_CONTROL, action="lock"

FILE_ACTION examples:
  "open downloads"          -> FILE_ACTION, action="open_folder", target="downloads"
  "open desktop folder"     -> FILE_ACTION, action="open_folder", target="desktop"
  "show documents"          -> FILE_ACTION, action="open_folder", target="documents"
  "open pictures"           -> FILE_ACTION, action="open_folder", target="pictures"
  "open my resume"          -> FILE_ACTION, action="open_file", target="resume"

SYSTEM_INFO examples:
  "how's my battery"        -> SYSTEM_INFO, metric="battery"
  "how much ram is free"    -> SYSTEM_INFO, metric="ram"
  "cpu usage"               -> SYSTEM_INFO, metric="cpu"
  "disk space"              -> SYSTEM_INFO, metric="disk"
  "system status"           -> SYSTEM_INFO, metric="all"

RUN_COMMAND examples:
  "run ipconfig"            -> RUN_COMMAND, command_name="ipconfig"
  "open task manager"       -> RUN_COMMAND, command_name="task manager"
  "disk cleanup"            -> RUN_COMMAND, command_name="disk cleanup"
  "ping google"             -> RUN_COMMAND, command_name="ping google"

Output format (strictly):
{"intent": "INTENT_NAME", "entities": {"key": "value"}, "confidence": "high"}

If no entity can be extracted, use an empty dict: {}
""".strip()


# ── Groq client (lazy init) ───────────────────────────────────────────────────

_client: Groq | None = None


def _get_client() -> Groq | None:
    """Return Groq client, or None if API key not configured."""
    global _client
    if _client is not None:
        return _client
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not set. AI parser unavailable.")
        return None
    _client = Groq(api_key=api_key)
    return _client


# ── Style profile injection ───────────────────────────────────────────────────

def _build_system_prompt() -> str:
    """
    Build the full system prompt by injecting the user's style profile.

    The style profile is extracted by Gemini (style_learner.py) from the
    user's chat history and stored in memory.json. Here we inject it into
    the Groq system prompt so the LLM understands casual/mixed inputs.
    """
    try:
        from jarvis.core import memory
        from jarvis.core import style_learner

        style_profile = memory.get("style_profile")
        if style_profile and isinstance(style_profile, dict):
            hint = style_learner.build_style_hint(style_profile)
            if hint:
                return _BASE_SYSTEM_PROMPT + "\n\n--- USER STYLE PROFILE ---\n" + hint
    except Exception:
        pass
    return _BASE_SYSTEM_PROMPT


# ── Main parse function ───────────────────────────────────────────────────────

def parse(user_input: str, recent_context: list[str] | None = None) -> tuple[str, dict]:
    """
    Parse user input using Groq LLM and return (intent, entities).

    Args:
        user_input:      Raw or normalized user text.
        recent_context:  Optional list of recent messages for context (max 5).

    Returns:
        (intent, entities) — same shape as intent_parser + entity_extractor.
        Returns (INTENT_UNKNOWN, {}) on any failure so the pipeline falls back.

    Examples:
        >>> parse("play kesariya")
        ('PLAY_MEDIA', {'song_name': 'kesariya'})

        >>> parse("bhai open chrome yaar")      # casual -- style profile helps
        ('OPEN_APP', {'app_name': 'chrome'})
    """
    client = _get_client()
    if not client:
        return INTENT_UNKNOWN, {}

    system_prompt = _build_system_prompt()

    # Build user message: optional context block + current command
    parts = []
    if recent_context:
        context_block = "Recent conversation context:\n" + "\n".join(
            f"  - {m}" for m in recent_context[-5:]
        )
        parts.append(context_block)
    parts.append(f"Current command: {user_input}")

    full_input = "\n\n".join(parts)

    try:
        response = _get_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": full_input},
            ],
            temperature=0.1,
            max_tokens=150,
        )

        raw = response.choices[0].message.content.strip()

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        intent   = data.get("intent", INTENT_UNKNOWN)
        entities = data.get("entities", {})

        if intent not in _VALID_INTENTS:
            logger.warning("Groq returned unknown intent: %s", intent)
            return INTENT_UNKNOWN, {}

        return intent, entities

    except json.JSONDecodeError as e:
        logger.error("Groq returned invalid JSON: %s | raw=%s", e, locals().get("raw", ""))
        return INTENT_UNKNOWN, {}

    except Exception as e:
        logger.error("Groq parser error: %s", e)
        return INTENT_UNKNOWN, {}


def is_available() -> bool:
    """Return True if the Groq AI parser is configured and ready."""
    return _get_client() is not None
