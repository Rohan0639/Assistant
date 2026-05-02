"""
core/memory.py

Phase 5 -- Persistent memory interface.

Responsibility:
    Read and write user preferences to config/memory.json.
    All other modules call this -- none touch the JSON file directly.

Design:
    - Single source of truth: config/memory.json
    - All reads/writes go through get() and set()
    - Memory is loaded once per session (cached in _cache)
    - Writes are flushed to disk immediately (no data loss)

Supported memory keys:
    user_name           -- user's preferred name
    favorite_song       -- default song to play
    favorite_app        -- default app to open
    favorite_website    -- default website to visit
    favorite_search     -- default search query
    shortcuts           -- custom named shortcuts (dict)
    usage_stats         -- intent usage counters (dict)
    last_seen           -- last session timestamp
"""

import json
import os
from datetime import datetime

# Absolute path to the memory file
_MEMORY_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "config", "memory.json"
)

# In-memory cache (loaded once per session)
_cache: dict | None = None


# ── Core I/O ─────────────────────────────────────────────────────────────────

def _load() -> dict:
    """Load memory from disk. Returns default dict if file missing."""
    global _cache
    if _cache is not None:
        return _cache
    try:
        with open(_MEMORY_FILE, "r", encoding="utf-8") as f:
            _cache = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        _cache = _default_memory()
    return _cache


def _save(data: dict) -> None:
    """Write memory to disk immediately."""
    global _cache
    _cache = data
    with open(_MEMORY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _default_memory() -> dict:
    """Return a blank memory template."""
    return {
        "user_name": "",
        "preferences": {
            "favorite_song": "",
            "favorite_app": "",
            "favorite_website": "",
            "favorite_search": "",
        },
        "shortcuts": {},
        "usage_stats": {
            "PLAY_MEDIA": 0, "OPEN_APP": 0,
            "OPEN_WEBSITE": 0, "SEARCH_WEB": 0,
            "WORKFLOW": 0, "REMEMBER": 0, "RECALL": 0,
        },
        "last_seen": "",
    }


# ── Public API ────────────────────────────────────────────────────────────────

def get(key: str, default=None):
    """
    Read a value from memory.

    Supports dot notation for nested keys:
        get("preferences.favorite_song")
        get("user_name")
        get("shortcuts")

    Args:
        key:     Key name (supports dot notation for nested dicts).
        default: Value to return if key not found.

    Returns:
        Stored value or default.
    """
    data = _load()
    parts = key.split(".")
    node = data
    for part in parts:
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node if node != "" else default


def set(key: str, value) -> None:
    """
    Write a value to memory and flush to disk.

    Supports dot notation for nested keys:
        set("user_name", "Rohan")
        set("preferences.favorite_song", "kesariya")
        set("shortcuts.work", "coding session")

    Args:
        key:   Key name (supports dot notation).
        value: Value to store.
    """
    data = _load()
    parts = key.split(".")

    node = data
    for part in parts[:-1]:
        if part not in node:
            node[part] = {}
        node = node[part]
    node[parts[-1]] = value

    _save(data)


def increment_stat(intent: str) -> None:
    """Increment the usage counter for a given intent."""
    data = _load()
    stats = data.get("usage_stats", {})
    stats[intent] = stats.get(intent, 0) + 1
    data["usage_stats"] = stats
    _save(data)


def update_last_seen() -> None:
    """Record current timestamp as last_seen."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    set("last_seen", now)


def get_user_name() -> str:
    """Return stored user name, or empty string if not set."""
    return get("user_name", "")


def get_all() -> dict:
    """Return the entire memory dict (for display/debug)."""
    return _load()


# ── REMEMBER helpers ──────────────────────────────────────────────────────────

# Maps what the AI extracts as key -> where to store it in memory
_KEY_MAP = {
    "name":             "user_name",
    "user_name":        "user_name",
    "favorite_song":    "preferences.favorite_song",
    "favorite_app":     "preferences.favorite_app",
    "favorite_website": "preferences.favorite_website",
    "favorite_search":  "preferences.favorite_search",
    "song":             "preferences.favorite_song",
    "app":              "preferences.favorite_app",
    "website":          "preferences.favorite_website",
}


def remember(key: str, value: str) -> tuple[bool, str]:
    """
    Store a user preference by key name.

    Args:
        key:   What type of thing to remember (e.g. "name", "favorite_song").
        value: The value to store.

    Returns:
        (success, response_message)
    """
    storage_key = _KEY_MAP.get(key.lower().strip(), f"preferences.{key}")
    set(storage_key, value)

    name = get_user_name()
    name_part = f", {name}" if name else ""

    return True, f"Got it{name_part}! I'll remember that {key} is '{value}'."


def recall(key: str) -> tuple[bool, str]:
    """
    Retrieve a stored preference by key name.

    Args:
        key: What to recall (e.g. "name", "favorite_song").

    Returns:
        (success, response_message)
    """
    storage_key = _KEY_MAP.get(key.lower().strip(), f"preferences.{key}")
    value = get(storage_key)

    name = get_user_name()
    name_part = f"{name}, your" if name else "Your"

    if not value:
        return False, f"I don't have '{key}' saved yet. Tell me and I'll remember!"

    return True, f"{name_part} {key} is '{value}'."


def recall_all() -> tuple[bool, str]:
    """Return a summary of everything stored in memory."""
    data = _load()
    name = data.get("user_name", "")
    prefs = data.get("preferences", {})
    shortcuts = data.get("shortcuts", {})
    stats = data.get("usage_stats", {})

    lines = []
    if name:
        lines.append(f"  Name: {name}")
    for k, v in prefs.items():
        if v:
            lines.append(f"  {k.replace('_', ' ').title()}: {v}")
    if shortcuts:
        lines.append(f"  Shortcuts: {', '.join(shortcuts.keys())}")

    top_intent = max(stats, key=stats.get) if stats else None
    if top_intent and stats.get(top_intent, 0) > 0:
        lines.append(f"  Most used: {top_intent} ({stats[top_intent]} times)")

    if not lines:
        return False, "I don't know anything about you yet. Tell me your name to get started!"

    return True, "Here's what I know about you:\n" + "\n".join(lines)
