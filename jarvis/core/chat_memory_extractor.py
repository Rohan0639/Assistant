"""
core/chat_memory_extractor.py

Silently extracts important personal facts from casual conversation and saves
them to JARVIS memory — things like friends' names, family members, and strong
personal preferences.

Design philosophy:
  - Only runs when the message contains keywords that *suggest* personal info
    (regex pre-check avoids unnecessary API calls for 90%+ of messages)
  - Runs in a background thread — never blocks the chat response
  - Saves ONLY high-value facts, not temporary states or generic chat

What gets extracted and saved:
  - People the user knows ("my friend Rahul") → contacts.Rahul = "friend"
  - Family members ("my sister Priya")        → contacts.Priya = "sister"
  - Strong preferences ("I love VS Code")     → preferences.hobby = "VS Code"
  - Hobbies explicitly stated                 → preferences.hobby = "..."

What does NOT get extracted:
  - Questions ("how are you?")
  - General knowledge ("what is Python?")
  - Temporary states ("I'm tired right now")
  - Things already in memory

Usage:
    from jarvis.core import chat_memory_extractor
    chat_memory_extractor.extract_async("my friend Rahul is here")
"""

import re
import json
import logging
import threading

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ── Keyword pre-filter ────────────────────────────────────────────────────────
# Only trigger extraction if the message likely contains personal info.
# This avoids making an API call for every single chat message.

_PERSONAL_INFO_PATTERNS = re.compile(
    r"\b(my\s+(friend|sister|brother|mom|dad|mother|father|uncle|aunt|cousin|boss|"
    r"colleague|co-worker|roommate|wife|husband|girlfriend|boyfriend|partner|mentor|"
    r"teacher|professor|classmate|teammate)\b"
    r"|i\s+(love|hate|really\s+like|adore|can't\s+stand|enjoy)\s+\w"
    r"|my\s+favorite\s+\w"
    r"|\bremember\s+that\b"
    r"|\bcall\s+me\b"
    r"|\bmy\s+name\s+is\b)",
    re.IGNORECASE
)

# ── Groq extraction prompt ────────────────────────────────────────────────────

_EXTRACTION_PROMPT = """
You are a personal fact extraction engine for an AI assistant.

Given the user's message, extract ONLY important personal facts worth remembering long-term.

Extract facts about:
  - People the user knows (friends, family, colleagues, etc.)
  - User's strong preferences explicitly stated ("I love X", "my favorite Y is Z")
  - User's hobbies or interests explicitly stated

Do NOT extract:
  - Temporary states ("I'm tired right now", "I'm bored")
  - Questions or requests
  - General knowledge queries
  - Vague or uncertain statements

Output format: JSON object using dot-notation keys.
  contacts.<PersonName> → their relationship to the user
  preferences.hobby     → their hobby/interest
  preferences.favorite_<thing> → their favorite X

Examples:
  Input: "my friend Rahul is coming over tonight"
  Output: {"contacts.Rahul": "friend"}

  Input: "my sister Priya just called me"
  Output: {"contacts.Priya": "sister"}

  Input: "I really love playing cricket on weekends"
  Output: {"preferences.hobby": "cricket"}

  Input: "my favorite show is Peaky Blinders"
  Output: {"preferences.favorite_show": "Peaky Blinders"}

  Input: "my boss is called Mr. Sharma"
  Output: {"contacts.Mr. Sharma": "boss"}

  Input: "how are you doing?"
  Output: {}

  Input: "what is the capital of France?"
  Output: {}

  Input: "I'm so bored right now"
  Output: {}

Return ONLY valid JSON. No explanation. No markdown. Empty dict {} if nothing to extract.
""".strip()


# ── Lazy Groq client ──────────────────────────────────────────────────────────

_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    import os
    from groq import Groq
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return None
    _client = Groq(api_key=api_key)
    return _client


# ── Core extraction logic ─────────────────────────────────────────────────────

def _should_attempt_extraction(text: str) -> bool:
    """Quick regex check — only run the expensive API call if worthwhile."""
    return bool(_PERSONAL_INFO_PATTERNS.search(text))


def _extract_and_save(user_input: str) -> dict:
    """
    Internal: call Groq to extract facts and save them to memory.
    Returns dict of saved facts (empty if nothing extracted).
    """
    client = _get_client()
    if not client:
        return {}

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": _EXTRACTION_PROMPT},
                {"role": "user",   "content": user_input},
            ],
            temperature=0.0,    # Deterministic for extraction
            max_tokens=120,
        )
        raw = response.choices[0].message.content.strip()

        # Strip accidental markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        facts = json.loads(raw)

        if not facts or not isinstance(facts, dict):
            return {}

        # Save each extracted fact to memory
        from jarvis.core import memory
        for key, value in facts.items():
            if key and value:
                memory.set(key, value)
                logger.info("Chat memory saved: %s = %r", key, value)

        return facts

    except Exception as e:
        logger.debug("Chat memory extraction skipped (%s): %s", type(e).__name__, e)
        return {}


# ── Public API ────────────────────────────────────────────────────────────────

def extract_async(user_input: str) -> None:
    """
    Non-blocking: check if the message likely contains personal info and,
    if so, extract and save it in a background thread.

    Designed to be fire-and-forget — never blocks the chat response.

    Args:
        user_input: The user's raw chat message.
    """
    if not _should_attempt_extraction(user_input):
        return   # Fast path — no personal info keywords detected

    thread = threading.Thread(
        target=_extract_and_save,
        args=(user_input,),
        daemon=True,
        name="jarvis-chat-memory",
    )
    thread.start()
