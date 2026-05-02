"""
core/chat_logger.py

Logs every user message to config/chat_log.jsonl.

Purpose:
    - Gives Gemini real examples of how Rohan types
    - Used to auto-extract a "style profile" after enough messages
    - Persists across all sessions so JARVIS gets smarter over time

Format (one JSON object per line):
    {"ts": "2026-05-02 10:15", "msg": "bhai play kesariya"}

Design:
    - Append-only: never deletes history
    - Lightweight: no external dependencies beyond stdlib
    - Safe: silently ignores write errors (assistant shouldn't crash over logging)
"""

import json
import os
from datetime import datetime

_LOG_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "chat_log.jsonl"
)

# How many messages before we attempt a style extraction
STYLE_EXTRACTION_THRESHOLD = 20


def log(user_message: str) -> None:
    """Append a single user message to the log file."""
    entry = {
        "ts": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "msg": user_message.strip()
    }
    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass  # Never let logging crash the assistant


def get_recent(n: int = 30) -> list[str]:
    """Return the last n user messages as plain strings."""
    try:
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
        entries = [json.loads(l)["msg"] for l in lines if l.strip()]
        return entries[-n:]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return []


def get_total_count() -> int:
    """Return total number of logged messages."""
    try:
        with open(_LOG_FILE, "r", encoding="utf-8") as f:
            return sum(1 for line in f if line.strip())
    except FileNotFoundError:
        return 0


def is_ready_for_style_learning() -> bool:
    """True if we have enough messages to extract a style profile."""
    return get_total_count() >= STYLE_EXTRACTION_THRESHOLD
