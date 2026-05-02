"""
core/entity_extractor.py

Responsibility: Extract the entity (subject) from a user command.

Strategy -- "Trigger Subtraction + Pattern Cleaning":
    1. Remove the matched trigger phrase from the clean input.
    2. Strip descriptor patterns  ("song called X" -> "X")   [Phase 2]
    3. Strip filler words from left and right of remainder.
    4. Map the remainder to the correct entity key for that intent.

Entity keys by intent:
    PLAY_MEDIA   -> { "song_name": "kesariya" }
    OPEN_APP     -> { "app_name": "chrome" }
    OPEN_WEBSITE -> { "website": "youtube" }
    SEARCH_WEB   -> { "query": "best python books" }

Design notes:
    - Returns an empty dict if no entity can be extracted.
    - Does NOT validate entity values (that is the action executor's job).
    - The matched_trigger comes from intent_parser.parse().
"""

import re

from jarvis.core.command import (
    INTENT_PLAY_MEDIA,
    INTENT_OPEN_APP,
    INTENT_OPEN_WEBSITE,
    INTENT_SEARCH_WEB,
    INTENT_UNKNOWN,
)


# ── Filler word lists ─────────────────────────────────────────────────────────
# Words between the trigger and the actual entity value.
# Stripped from the LEFT side of the remainder.
# Order: longer phrases before shorter ones.

_LEFT_FILLERS: list[str] = [
    # Phrases
    "for me",
    "for",
    "up the",
    "up a",
    "up",
    # Articles + determiners
    "some",
    "any",
    "the",
    "a",
    "an",
    # Pronouns
    "me",
    "my",
    "our",
]

# Words that appear AFTER the entity (trailing noise).
# Stripped from the RIGHT side of the remainder.

_RIGHT_FILLERS: list[str] = [
    "right now",        # longer first
    "for me",
    "please",
    "now",
    "thanks",
    "thank you",
    "asap",
]


# ── [Phase 2] Descriptor pattern regex ───────────────────────────────────────
# Handles: "song called X", "app named X", "website called X", etc.
# Matches a descriptor noun + "called"/"named" and strips it,
# leaving only the actual target value X.
#
# Examples:
#   "song called kesariya"        -> "kesariya"
#   "app named chrome"            -> "chrome"
#   "website called github"       -> "github"
#   "something called blinding"   -> "blinding"
#   "track by the weeknd"         -> kept as-is (artist phrasing is useful)

_DESCRIPTOR_PATTERN = re.compile(
    r"^(?:song|songs|track|tracks|music|tune|tunes|"
    r"app|apps|application|applications|program|programs|"
    r"website|site|page|"
    r"something|anything|stuff)\s+"
    r"(?:called|named|titled|known as|by the name of)\s+",
    re.IGNORECASE,
)

# [Phase 2] Strip "about" prefix left by "tell me about" trigger splits
# e.g. trigger="tell me about" leaves "" remainder, so this is rarely needed,
# but "what about X" -> remainder starts with "about X"
_ABOUT_PREFIX = re.compile(r"^about\s+", re.IGNORECASE)


# ── Core functions ─────────────────────────────────────────────────────────────

def _strip_trigger(clean_input: str, trigger: str) -> str:
    """
    Remove the trigger phrase from the clean input string.

    Finds the trigger, returns everything after it.

    Example:
        clean_input = "can you play kesariya"
        trigger     = "can you play"
        result      = "kesariya"
    """
    idx = clean_input.find(trigger)
    if idx == -1:
        return clean_input  # Safety fallback

    remainder = clean_input[idx + len(trigger):].strip()
    return remainder


def _strip_descriptor(text: str) -> str:
    """
    [Phase 2] Strip 'TYPE called/named VALUE' patterns, returning just VALUE.

    Examples:
        "song called kesariya"     -> "kesariya"
        "app named chrome"         -> "chrome"
        "something called youtube" -> "youtube"
        "kesariya"                 -> "kesariya"  (unchanged, no pattern)
    """
    result = _DESCRIPTOR_PATTERN.sub("", text).strip()
    return result


def _strip_fillers_left(text: str) -> str:
    """
    Remove one leading filler word/phrase from the left side.
    Only one strip to avoid over-removing meaningful words.
    """
    for filler in _LEFT_FILLERS:
        if text.startswith(filler + " ") or text == filler:
            text = text[len(filler):].strip()
            break
    return text.strip()


def _strip_fillers_right(text: str) -> str:
    """
    Remove all trailing filler words from the right side.
    Loops until no more right fillers are found.
    """
    changed = True
    while changed:
        changed = False
        for filler in _RIGHT_FILLERS:
            if text.endswith(" " + filler) or text == filler:
                text = text[: -(len(filler))].strip()
                changed = True
                break
    return text.strip()


def _strip_fillers(text: str) -> str:
    """Convenience wrapper: strip both left and right fillers."""
    text = _strip_fillers_left(text)
    text = _strip_fillers_right(text)
    return text


def extract(intent: str, clean_input: str, matched_trigger: str) -> dict:
    """
    Extract entities from a classified command.

    Args:
        intent:          The classified intent (e.g. "PLAY_MEDIA").
        clean_input:     Normalized user text from input_handler.
        matched_trigger: The trigger phrase that matched, from intent_parser.

    Returns:
        A dict of extracted entities, e.g. {"song_name": "kesariya"}.
        Returns {} if intent is UNKNOWN or no entity found.

    Examples:
        >>> extract("PLAY_MEDIA", "play a song called kesariya", "play a")
        {'song_name': 'kesariya'}

        >>> extract("OPEN_APP", "open an app called chrome please", "open")
        {'app_name': 'chrome'}

        >>> extract("SEARCH_WEB", "what is machine learning", "what is")
        {'query': 'machine learning'}

        >>> extract("SEARCH_WEB", "how to center a div", "how to")
        {'query': 'center a div'}
    """
    if intent == INTENT_UNKNOWN or not matched_trigger:
        return {}

    # Step 1: Remove the trigger phrase
    remainder = _strip_trigger(clean_input, matched_trigger)

    # Step 2: Strip LEFT filler words first (clears 'an', 'a', 'the' etc.)
    #          so descriptor pattern fires correctly on what follows
    remainder = _strip_fillers_left(remainder)

    # Step 3: [Phase 2] Strip descriptor patterns ("song called X" -> "X")
    remainder = _strip_descriptor(remainder)

    # Step 4: Strip RIGHT filler words ("please", "now", "for me" etc.)
    remainder = _strip_fillers_right(remainder)

    # Step 4: Guard — nothing left after stripping
    if not remainder:
        return {}

    # Step 5: Map to correct entity key
    if intent == INTENT_PLAY_MEDIA:
        return {"song_name": remainder}

    elif intent == INTENT_OPEN_APP:
        return {"app_name": remainder}

    elif intent == INTENT_OPEN_WEBSITE:
        return {"website": remainder}

    elif intent == INTENT_SEARCH_WEB:
        return {"query": remainder}

    return {}
