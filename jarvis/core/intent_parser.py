"""
core/intent_parser.py

Responsibility: Classify user intent from a normalized input string.

Algorithm:
    Scans the cleaned input for trigger phrases defined in config/intents.py.
    Trigger phrases within each intent are ordered longest-first (in config),
    ensuring more specific phrases match before general single-word ones.

Returns:
    A tuple of (intent_id, matched_trigger):
        intent_id       — one of the INTENT_* constants from command.py
        matched_trigger — the exact phrase that triggered the match,
                          used by entity_extractor.py to isolate the entity.
    On no match: (INTENT_UNKNOWN, "")

Design notes:
    - Intent priority order matters. OPEN_WEBSITE is checked before OPEN_APP
      because "go to youtube" should not trigger OPEN_APP even though "open"
      might appear in future inputs.
    - The parser does NOT modify the Command object directly. That is
      the pipeline's job.
    - No regex here — plain substring matching is fast, readable, and enough.
"""

from jarvis.core.command import (
    INTENT_PLAY_MEDIA,
    INTENT_OPEN_APP,
    INTENT_OPEN_WEBSITE,
    INTENT_SEARCH_WEB,
    INTENT_UNKNOWN,
)
from jarvis.config.intents import INTENT_TRIGGERS


# Intent evaluation order matters.
# More specific intents must be checked before broader ones.
# Example: OPEN_WEBSITE before OPEN_APP — both can respond to "open youtube"
#          but OPEN_WEBSITE is the correct classification.
_INTENT_PRIORITY: list[str] = [
    INTENT_PLAY_MEDIA,
    INTENT_OPEN_WEBSITE,   # ← before OPEN_APP (more specific)
    INTENT_OPEN_APP,
    INTENT_SEARCH_WEB,
]


def parse(clean_input: str) -> tuple[str, str]:
    """
    Classify the intent of a normalized user input.

    Args:
        clean_input: Normalized text from input_handler.handle().

    Returns:
        (intent_id, matched_trigger)
        e.g. ("PLAY_MEDIA", "play") for input "play kesariya"
        e.g. ("UNKNOWN", "")        for input "hello there"

    Examples:
        >>> parse("play kesariya")
        ('PLAY_MEDIA', 'play')

        >>> parse("can you open chrome")
        ('OPEN_APP', 'can you open')

        >>> parse("search for best python books")
        ('SEARCH_WEB', 'search for')

        >>> parse("go to youtube")
        ('OPEN_WEBSITE', 'go to')

        >>> parse("hello there")
        ('UNKNOWN', '')
    """
    if not clean_input:
        return INTENT_UNKNOWN, ""

    for intent in _INTENT_PRIORITY:
        triggers = INTENT_TRIGGERS.get(intent, [])
        # Triggers are already ordered longest-first in config/intents.py
        for trigger in triggers:
            if trigger in clean_input:
                return intent, trigger

    return INTENT_UNKNOWN, ""
