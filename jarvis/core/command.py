"""
core/command.py

The Command Object — the shared data contract of the entire pipeline.

Every module reads from and writes to this object.
Think of it as the "baton" passed between pipeline stages.

Design note:
  We use a plain class (not dataclass) so we can add validation
  and helper methods cleanly as the project grows.
"""

from typing import Optional


# ── Intent constants ──────────────────────────────────────────────────────────
# Define intents as module-level constants.
# This avoids string literals scattered across the codebase
# and gives you autocomplete + prevents typo bugs.

INTENT_PLAY_MEDIA      = "PLAY_MEDIA"
INTENT_OPEN_APP        = "OPEN_APP"
INTENT_OPEN_WEBSITE    = "OPEN_WEBSITE"
INTENT_SEARCH_WEB      = "SEARCH_WEB"
INTENT_WORKFLOW        = "WORKFLOW"         # Phase 4
INTENT_REMEMBER        = "REMEMBER"         # Phase 5
INTENT_RECALL          = "RECALL"           # Phase 5
INTENT_REMINDER        = "REMINDER"         # Phase 6
INTENT_SYSTEM_CONTROL  = "SYSTEM_CONTROL"   # Phase 7 - volume, sleep, shutdown
INTENT_FILE_ACTION     = "FILE_ACTION"      # Phase 7 - open folders/files
INTENT_SYSTEM_INFO     = "SYSTEM_INFO"      # Phase 7 - battery, RAM, CPU
INTENT_RUN_COMMAND     = "RUN_COMMAND"      # Phase 7 - whitelisted shell commands
INTENT_UNKNOWN         = "UNKNOWN"

# ── Intent aliases (LLM hallucination protection) ─────────────────────────────
# LLMs sometimes return non-canonical intent names (e.g. PLAY_MUSIC instead of
# PLAY_MEDIA). Map all known variants → the canonical constant so the executor
# never has to handle raw strings from the AI directly.
INTENT_ALIASES: dict[str, str] = {
    # Media variants
    "PLAY_MUSIC":       INTENT_PLAY_MEDIA,
    "PLAY_SONG":        INTENT_PLAY_MEDIA,
    "MUSIC":            INTENT_PLAY_MEDIA,
    "PLAY_VIDEO":       INTENT_PLAY_MEDIA,
    "PLAY_AUDIO":       INTENT_PLAY_MEDIA,
    # App variants
    "LAUNCH_APP":       INTENT_OPEN_APP,
    "OPEN_APPLICATION": INTENT_OPEN_APP,
    "START_APP":        INTENT_OPEN_APP,
    # Website variants
    "OPEN_URL":         INTENT_OPEN_WEBSITE,
    "BROWSE":           INTENT_OPEN_WEBSITE,
    "NAVIGATE":         INTENT_OPEN_WEBSITE,
    # Search variants
    "WEB_SEARCH":       INTENT_SEARCH_WEB,
    "GOOGLE":           INTENT_SEARCH_WEB,
    # Unknown variants
    "INTENT_UNKNOWN":   INTENT_UNKNOWN,
    "NONE":             INTENT_UNKNOWN,
    "CHAT":             INTENT_UNKNOWN,
}

ALL_INTENTS = {
    INTENT_PLAY_MEDIA,
    INTENT_OPEN_APP,
    INTENT_OPEN_WEBSITE,
    INTENT_SEARCH_WEB,
    INTENT_WORKFLOW,
    INTENT_REMEMBER,
    INTENT_RECALL,
    INTENT_REMINDER,
    INTENT_SYSTEM_CONTROL,
    INTENT_FILE_ACTION,
    INTENT_SYSTEM_INFO,
    INTENT_RUN_COMMAND,
    INTENT_UNKNOWN,
}


# ── Command Object ────────────────────────────────────────────────────────────

class Command:
    """
    Represents a single user command as it flows through the pipeline.

    Lifecycle:
        1. Created by pipeline.py with just raw_input
        2. input_handler.py fills clean_input
        3. intent_parser.py fills intent
        4. entity_extractor.py fills entities
        5. action_executor.py reads intent + entities and acts
    """

    def __init__(self, raw_input: str):
        # Stage 1: Set by Input Handler
        self.raw_input: str = raw_input
        self.clean_input: str = ""

        # Stage 2: Set by Intent Parser
        self.intent: str = INTENT_UNKNOWN

        # Stage 3: Set by Entity Extractor
        # A flexible dict — keys depend on intent:
        #   PLAY_MEDIA   → { "song_name": "kesariya" }
        #   OPEN_APP     → { "app_name": "chrome" }
        #   OPEN_WEBSITE → { "website": "youtube.com" }
        #   SEARCH_WEB   → { "query": "best python frameworks" }
        self.entities: dict = {}

        # Stage 4: Set by Action Executor
        # Whether the action was successfully performed
        self.success: bool = False

        # Human-readable message for the Response Layer
        self.response: str = ""

        # Response mode — determines how the UI renders this response
        # "action" → command was executed (shows [OK]/[!] prefix, green/red color)
        # "chat"   → conversational reply (no prefix, blue color)
        self.mode: str = "action"

    def is_resolved(self) -> bool:
        """Returns True if intent was successfully identified."""
        return self.intent != INTENT_UNKNOWN

    def __repr__(self) -> str:
        """Clean debug output — invaluable during development."""
        return (
            f"Command(\n"
            f"  raw_input   = {self.raw_input!r}\n"
            f"  clean_input = {self.clean_input!r}\n"
            f"  intent      = {self.intent}\n"
            f"  entities    = {self.entities}\n"
            f"  success     = {self.success}\n"
            f"  response    = {self.response!r}\n"
            f")"
        )
