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

from jarvis.core import groq_client

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
You are JARVIS, a precise and reliable AI assistant.

Your job is to understand the user's request and return structured actions WITHOUT breaking execution.

---
CRITICAL RULES (DO NOT BREAK):
* Only return actions that are explicitly requested in the CURRENT user input
* NEVER reuse or repeat actions from previous messages
* NEVER assume previous tasks should continue
* If the user does not ask → DO NOT include that action

---
CAPABILITY AWARENESS:
* ONLY use actions that are supported by the system
* Supported system controls MUST use intent: "SYSTEM_CONTROL" and set the target to:
  * 'set_volume', 'volume_up', 'volume_down', 'mute', 'unmute'
  * 'set_brightness'
* If a request is unsupported → return no action and respond conversationally

---
VOLUME & BRIGHTNESS RULES (STRICT):
* Valid range is 0–100
* If user says "set volume/brightness to X":
  * If X > 100 → DO NOT execute, return no action and explain briefly
  * If X is valid → use absolute set with target "set_volume" or "set_brightness" and value X.
* If user says "volume" or "increase volume":
  * treat as relative increase (no fixed value required)
* NEVER auto-convert invalid values (e.g., 220 → 100 is NOT allowed)

---
MULTI-INTENT RULES:
* Only include actions clearly present in the current input
* Do NOT merge with previous actions
* Each action must be independent and relevant

---
BROWSER / MEDIA RULES:
* You DO NOT have control over existing browser tabs
* NEVER say:
  * "I will use the same tab"
  * "I will not open a new tab"
* Always give realistic responses:
  * e.g., "Opening YouTube and playing it for you"

---
RESPONSE RULES:
* Be natural and human-like
* DO NOT claim something is done unless action is valid
---
APP VS WEBSITE VS MEDIA RULES:
* Desktop apps (chrome, calc, notepad, vs code) -> use OPEN_APP
* Websites (youtube, netflix, github, google) -> use OPEN_WEBSITE
* Playing music/videos/songs ("play dude ost", "play some jazz") -> use PLAY_MEDIA (NEVER use PLAY_MUSIC, PLAY_SONG, or any other variant)
* NEVER use OPEN_APP for websites.
* The ONLY valid intent strings are: PLAY_MEDIA, OPEN_APP, OPEN_WEBSITE, SEARCH_WEB, SYSTEM_CONTROL, FILE_ACTION, SYSTEM_INFO, RUN_COMMAND, REMEMBER, RECALL, WORKFLOW, UNKNOWN.

---
OUTPUT FORMAT (STRICT JSON ONLY):
{
  "emotion": "bored/sad/stressed/happy/neutral",
  "actions": [
    {
      "intent": "OPEN_APP",
      "target": "chrome",
      "value": null,
      "search_query": null
    },
    {
      "intent": "OPEN_WEBSITE",
      "target": "youtube",
      "value": null,
      "search_query": null
    },
    {
      "intent": "PLAY_MEDIA",
      "target": null,
      "value": null,
      "search_query": "dude ost"
    }
  ],
  "response": "natural human-like response"
}

---
IMPORTANT:
* 'target' is the app, website, or action target (e.g. 'chrome', 'youtube', 'set_volume').
* 'value' is for numbers (e.g. 50 for volume).
* 'search_query' is for song names or search terms.
* If no valid action -> return "actions": []
* DO NOT guess missing values
* DO NOT hallucinate capabilities
* DO NOT include previous context actions
""".strip()

# ── Groq client configuration ─────────────────────────────────────────────────

def is_available() -> bool:
    """Return True if the Groq AI parser is configured and ready."""
    return groq_client.is_available()


# ── Style profile injection ───────────────────────────────────────────────────

def _build_system_prompt() -> str:
    from jarvis.core import memory
    style_profile = memory.get("style_profile", "")
    prompt = _BASE_SYSTEM_PROMPT
    if style_profile:
        prompt += f"\n\nUSER'S PREFERRED STYLE:\n{style_profile}"
    return prompt


# ── Parsing ───────────────────────────────────────────────────────────────────

def parse(
    user_input: str,
    recent_context: list[str] | None = None
) -> tuple[list[dict], str, str]:
    """
    Parse natural language into a list of actionable intents + conversational response.

    Args:
        user_input: The raw string from the user.
        recent_context: Optional rolling window of the conversation.

    Returns:
        (actions, ai_response, emotion)
        actions is a list of dicts: [{"intent": ..., "target": ..., "value": ..., "search_query": ...}]
        ai_response is the human-like response generated by the LLM.
        emotion is the detected user emotion.
    """
    if not is_available():
        return [], "", "neutral"

    system_prompt = _build_system_prompt()
    messages: list[dict] = [{"role": "system", "content": system_prompt}]

    if recent_context:
        history_str = "\n".join(recent_context)
        context_prompt = (
            f"--- RECENT CONVERSATION HISTORY ---\n{history_str}\n"
            "--- END HISTORY ---\n\n"
            "CRITICAL: Use the history above ONLY to understand context (like 'open it', or 'no'). "
            "DO NOT output actions for past requests. ONLY output actions for the CURRENT user request below. "
            "You MUST still output STRICT JSON."
        )
        messages.append({"role": "system", "content": context_prompt})

    messages.append({"role": "user", "content": user_input})

    try:
        response = groq_client.get_completion(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,   # Allow slightly more creativity for the natural response
            max_tokens=400,
        )

        raw = response.choices[0].message.content.strip()

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        actions = data.get("actions", [])
        ai_response = data.get("response", "")
        emotion = data.get("emotion", "neutral")
        
        # If no actions array but intent is CHAT, handle gracefully
        if not actions and data.get("intent") == "CHAT":
            actions = [{"intent": "CHAT"}]

        return actions, ai_response, emotion

    except json.JSONDecodeError as e:
        logger.error("Groq returned invalid JSON: %s | raw=%s", e, locals().get("raw", ""))
        return INTENT_UNKNOWN, {}, ""

    except Exception as e:
        logger.error("Groq parser error: %s", e)
        return INTENT_UNKNOWN, {}, ""

