"""
core/input_handler.py

Responsibility: Accept raw user text, return a clean normalized string.

This is the FIRST stage of the pipeline. It runs before any parsing.

What it does:
    1. Strip leading/trailing whitespace
    2. Lowercase the entire string
    3. Remove punctuation that doesn't affect meaning
    4. Collapse multiple spaces into one

What it does NOT do:
    - Detect intent (that's intent_parser.py)
    - Extract entities (that's entity_extractor.py)
    - Modify the Command object (that's pipeline.py's job)
"""

import re


# Punctuation characters to remove.
# We keep hyphens (-) and apostrophes (') because they affect meaning:
#   "vs-code" should stay as "vs code" after replacement
#   "don't" should stay as "don't" (contraction, not noise)
_REMOVE_PUNCTUATION = re.compile(r"[^\w\s\'-]")

# Collapse 2+ spaces → single space
_COLLAPSE_SPACES = re.compile(r"\s+")

# Replace hyphens with spaces so "vs-code" → "vs code"
_HYPHEN_TO_SPACE = re.compile(r"-")


def normalize(raw: str) -> str:
    """
    Normalize raw user input for downstream processing.

    Args:
        raw: The exact string the user typed.

    Returns:
        A cleaned, lowercase, single-spaced string.

    Examples:
        >>> normalize("  Can you PLAY Kesariya!!  ")
        'can you play kesariya'

        >>> normalize("Open VS-Code please.")
        'open vs code please'

        >>> normalize("Search for   best Python frameworks?")
        'search for best python frameworks'
    """
    if not raw or not raw.strip():
        return ""

    text = raw.strip()           # Step 1: Remove surrounding whitespace
    text = text.lower()          # Step 2: Lowercase
    text = _HYPHEN_TO_SPACE.sub(" ", text)      # Step 3a: Hyphens → spaces
    text = _REMOVE_PUNCTUATION.sub("", text)    # Step 3b: Remove noise punctuation
    text = _COLLAPSE_SPACES.sub(" ", text)      # Step 4: Collapse spaces
    text = text.strip()          # Final: Clean up any edge-case trailing space

    return text


def handle(raw_input: str) -> str:
    """
    Public entry point for the pipeline.

    Args:
        raw_input: Raw user text (directly from input prompt).

    Returns:
        Normalized string ready for intent parsing.
        Returns empty string if input is blank/whitespace only.
    """
    return normalize(raw_input)
