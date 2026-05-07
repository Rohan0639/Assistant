"""
core/style_learner.py

Learns the user's personal texting/typing style from their chat history.
Uses Gemini (google-genai SDK) ONLY for this one job — Groq handles commands.

How it works:
    1. After STYLE_EXTRACTION_THRESHOLD messages are logged, this module
       sends a sample of recent messages to Gemini and asks it to describe
       how the user communicates.
    2. The resulting "style profile" is saved to memory.json under
       "style_profile" so it persists across sessions.
    3. ai_parser.py reads this profile and injects it into the Groq system
       prompt, making the LLM understand casual/mixed-language inputs better.

Style profile schema (stored in memory.json):
    {
        "style_profile": {
            "tone":        "casual and friendly",
            "patterns":    ["skips grammar", "uses short phrases", "says bhai"],
            "examples":    ["bhai play kuch", "open chrome yaar"],
            "summary":     "Rohan types casually with Hindi-English mix...",
            "extracted_at": "2026-05-02 10:15"
        }
    }
"""

import json
import logging
import os
from datetime import datetime

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

from jarvis.core import groq_client

_STYLE_EXTRACTION_PROMPT = """
You are analyzing how a specific person types messages to their personal AI assistant.

Here are their recent messages (most recent last):
---
{messages}
---

Based ONLY on these messages, create a style profile describing how this person communicates.
Return ONLY a valid JSON object with these exact keys:

{
  "tone": "one phrase describing their overall tone (e.g. 'casual and informal')",
  "patterns": ["list", "of", "observed", "typing patterns"],
  "examples": ["2-3 example phrases they commonly use"],
  "summary": "2-3 sentence description of how they type and phrase requests"
}

Focus on: abbreviations, slang, mixing languages (Hindi-English etc), grammar shortcuts,
directness, common phrases, sentence length, and punctuation habits.
Return ONLY the JSON. No explanation. No markdown fences.
""".strip()


def extract_style_profile(recent_messages: list[str]) -> dict | None:
    """
    Call Groq to analyze recent messages and extract a style profile.

    Args:
        recent_messages: List of raw user message strings.

    Returns:
        Style profile dict, or None on failure.
    """
    if not groq_client.is_available():
        logger.info("Style learner: No Groq keys configured, skipping.")
        return None

    if len(recent_messages) < 5:
        return None

    sample = "\n".join(recent_messages[-40:])
    prompt = _STYLE_EXTRACTION_PROMPT.format(messages=sample)

    try:
        response = groq_client.get_completion(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=250,
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        profile = json.loads(raw)
        profile["extracted_at"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        return profile

    except Exception as e:
        logger.warning("Style extraction skipped (Groq error: %s)", e)
        return None


def build_style_hint(style_profile: dict) -> str:
    """
    Convert a style profile dict into a short paragraph for the Groq system prompt.

    Returns:
        A few lines describing how the user types, injected into the LLM prompt.
    """
    if not style_profile:
        return ""

    tone     = style_profile.get("tone", "")
    patterns = style_profile.get("patterns", [])
    examples = style_profile.get("examples", [])
    summary  = style_profile.get("summary", "")

    lines = []
    if tone:
        lines.append(f"User communication style: {tone}.")
    if summary:
        lines.append(summary)
    if patterns:
        lines.append("Common patterns: " + "; ".join(patterns) + ".")
    if examples:
        lines.append("Example phrases they use: " + ", ".join(f'"{e}"' for e in examples) + ".")

    return "\n".join(lines)
