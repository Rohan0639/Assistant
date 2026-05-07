"""
config/intents.py

Intent trigger phrase definitions.

Structure:
    INTENT_TRIGGERS is a dict mapping each intent ID to a list of
    trigger phrases. The Intent Parser checks if any of these phrases
    appear in the user's cleaned input.

Design rules:
    1. Phrases are lowercase -- Input Handler normalizes before matching.
    2. Longer phrases come FIRST in each list.
       Reason: "listen to" must be checked before "listen"
       so it doesn't get partially swallowed.
    3. This file has ZERO imports and ZERO logic -- pure data only.

Phase 2 additions are marked with [P2]
"""

INTENT_TRIGGERS: dict[str, list[str]] = {

    # -- PLAY_MEDIA ------------------------------------------------------------
    # User wants to play audio or video content.
    "PLAY_MEDIA": [
        # Phase 1
        "play me",
        "play some",
        "play the",
        "play a",
        "listen to",
        "put on",
        "i want to hear",
        "i want to listen",
        "can you play",
        "please play",
        # Phase 2 additions
        "i would like to hear",         # [P2] from "i'd like to hear" expansion
        "i would like to listen",       # [P2]
        "i would like to play",         # [P2]
        "i would love to hear",         # [P2]
        "want to hear",                 # [P2] from wanna hear expansion
        "want to listen",               # [P2] from wanna listen expansion
        "want to play",                 # [P2] from wanna play expansion
        "start playing",                # [P2]
        "queue up",                     # [P2] music queue phrasing
        "add to queue",                 # [P2]
        "blast some",                   # [P2] informal
        "blast",                        # [P2]
        "stream",                       # [P2]
        # Shortest / most general -- always last
        "play",
    ],

    # -- OPEN_APP --------------------------------------------------------------
    # User wants to launch a desktop application.
    "OPEN_APP": [
        # Phase 1
        "launch the",
        "launch my",
        "open the",
        "open my",
        "open up",
        "start up",
        "can you open",
        "please open",
        # Phase 2 additions
        "i need to open",               # [P2]
        "i want to open",               # [P2]
        "i would like to open",         # [P2]
        "i need to launch",             # [P2]
        "i want to launch",             # [P2]
        "can you launch",               # [P2]
        "please launch",                # [P2]
        "run the",                      # [P2] developer phrasing
        "run my",                       # [P2]
        "execute",                      # [P2] power-user phrasing
        # Shortest / most general -- always last
        "launch",
        "start",
        "open",
        "run",                          # [P2]
    ],

    # -- OPEN_WEBSITE ----------------------------------------------------------
    # User wants to navigate to a specific website.
    "OPEN_WEBSITE": [
        # Phase 1
        "go to website",
        "open website",
        "navigate to",
        "take me to",
        "go to",
        "visit",
        # Phase 2 additions
        "i want to go to",              # [P2]
        "i want to visit",              # [P2]
        "i would like to visit",        # [P2]
        "can you take me to",           # [P2]
        "open the website",             # [P2]
        "show me the website",          # [P2]
        "load",                         # [P2] e.g. "load youtube"
    ],

    # -- SEARCH_WEB ------------------------------------------------------------
    # User wants to run a web search for information.
    "SEARCH_WEB": [
        # Phase 1
        "look up",
        "search for",
        "find me",
        "google for",
        "can you search",
        # Phase 2 additions
        "i want to know about",         # [P2] knowledge query phrasing
        "i want to search for",         # [P2]
        "i would like to know",         # [P2]
        "tell me about",                # [P2]
        "what is",                      # [P2] question phrasing
        "what are",                     # [P2]
        "who is",                       # [P2]
        "where is",                     # [P2]
        "how to",                       # [P2]
        "how do i",                     # [P2]
        "can you find",                 # [P2]
        "look for",                     # [P2]
        # Shortest / most general -- always last
        "search",
        "google",
        "find",
    ],

    # -- SYSTEM_CONTROL --------------------------------------------------------
    # User wants to control volume, power, or screen lock.
    "SYSTEM_CONTROL": [
        # Volume — longer phrases first
        "turn up the volume",
        "turn down the volume",
        "increase the volume",
        "decrease the volume",
        "raise the volume",
        "lower the volume",
        "set volume to",
        "set the volume to",
        "change volume to",
        "volume up",
        "volume down",
        "volume set",
        "volume mute",
        "turn up",
        "turn down",
        "increase volume",
        "decrease volume",
        "louder",
        "quieter",
        "unmute",
        "mute",
        # Power
        "shut down",
        "turn off the pc",
        "turn off pc",
        "power off",
        "shutdown",
        "restart the pc",
        "restart pc",
        "restart",
        "reboot",
        "go to sleep",
        "sleep mode",
        "sleep",
        "suspend",
        # Screen lock
        "lock the screen",
        "lock screen",
        "lock my pc",
        "lock pc",
        "lock",
    ],
}
