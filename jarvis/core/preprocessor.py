"""
core/preprocessor.py

Phase 2 addition — sits between Input Handler and Intent Parser.

Responsibility: Rewrite natural/informal language into forms the
Intent Parser already knows how to handle.

Three stages (run in order):
    1. Strip greeting/assistant-name prefixes  ("hey jarvis," -> "")
    2. Expand contractions and informal words  ("wanna" -> "want to")
    3. Strip polite command prefixes           ("could you please" -> "")

Design principle:
    This module ONLY rewrites text. It does NOT classify intent or
    extract entities. Output is still a plain string.

Why a separate module (not baked into input_handler):
    Input Handler handles formatting noise (whitespace, casing, punctuation).
    Preprocessor handles linguistic/semantic noise.
    These are different concerns and should remain separate.
"""

import re


# ── 1. Greeting / assistant-name prefixes ─────────────────────────────────────
# Patterns to strip from the START of the string only.
# Ordered longest-first to avoid partial stripping.

_GREETING_PATTERNS: list[str] = [
    "hey jarvis",
    "ok jarvis",
    "okay jarvis",
    "jarvis",
    "hey there",
    "hey",
    "hi",
    "hello",
    "yo",
]


# ── 2. Contraction / informal word expansion ──────────────────────────────────
# Maps informal words -> formal equivalents.
# These are replaced ANYWHERE in the string (not just the start).
# Ordered to avoid substring conflicts (longer entries first).

_CONTRACTIONS: dict[str, str] = {
    # Play-related
    "wanna hear":    "want to hear",
    "wanna listen":  "want to listen",
    "wanna play":    "want to play",
    "wanna":         "want to",
    "lemme hear":    "let me hear",
    "lemme listen":  "let me listen",
    "lemme":         "let me",
    "gonna":         "going to",
    "gotta":         "got to",
    "hafta":         "have to",
    "i'd like to":   "i would like to",
    "i'd love to":   "i would like to",
    "i'd":           "i would",
    "can't":         "cannot",
    "don't":         "do not",
    "i'm":           "i am",
    "i've":          "i have",
    # Open/launch-related
    "pull up":       "go to",       # website context — maps to OPEN_WEBSITE
    "load up":       "go to",       # website context — maps to OPEN_WEBSITE
    "bring up":      "open",
    "boot up":       "launch",
    "fire up":       "launch",
    "spin up":       "launch",
    # Search-related
    "look for":      "search for",
    "look into":     "search for",
    "hunt for":      "search for",
    "show me":       "find",
    # Website-related
    "take me":       "go",
    "bring me":      "go",
    "head to":       "go to",
    "navigate":      "go to",
}


# ── 3. Polite command prefixes ─────────────────────────────────────────────────
# Phrases at the START of the string that signal politeness but not intent.
# Ordered longest-first.

_POLITE_PREFIXES: list[str] = [
    "could you please",
    "would you please",
    "can you please",
    "will you please",
    "could you kindly",
    "would you kindly",
    "could you",
    "would you",
    "will you",
    "can you",
    "please",
    "kindly",
]


# ── Core functions ─────────────────────────────────────────────────────────────

def _strip_greeting(text: str) -> str:
    """Remove greeting/name prefix from the start of the text."""
    for greeting in _GREETING_PATTERNS:
        # Match at the start, optionally followed by comma/space
        pattern = r"^" + re.escape(greeting) + r"[\s,!]*"
        result = re.sub(pattern, "", text).strip()
        if result != text:
            return result
    return text


def _expand_contractions(text: str) -> str:
    """Replace informal words with formal equivalents anywhere in text."""
    for informal, formal in _CONTRACTIONS.items():
        # Word-boundary aware replacement to avoid partial matches
        pattern = r"\b" + re.escape(informal) + r"\b"
        text = re.sub(pattern, formal, text)
    return text


def _strip_polite_prefix(text: str) -> str:
    """Remove polite filler phrase from the start of the string."""
    for prefix in _POLITE_PREFIXES:
        if text.startswith(prefix + " ") or text == prefix:
            text = text[len(prefix):].strip()
            break  # Only strip one prefix
    return text


def process(clean_input: str) -> str:
    """
    Apply all preprocessing transformations to a normalized input string.

    Should be called AFTER input_handler.handle() and BEFORE intent_parser.parse().

    Args:
        clean_input: Already-normalized string from input_handler.

    Returns:
        Preprocessed string, still lowercase and clean.

    Examples:
        >>> process("hey jarvis play kesariya")
        'play kesariya'

        >>> process("could you please open chrome")
        'open chrome'

        >>> process("wanna hear blinding lights")
        'want to hear blinding lights'

        >>> process("hey could you wanna play something")
        'want to play something'
    """
    if not clean_input:
        return clean_input

    text = clean_input

    # Apply in order: greeting → contractions → polite prefix
    text = _strip_greeting(text)
    text = _expand_contractions(text)
    text = _strip_polite_prefix(text)

    return text.strip()
