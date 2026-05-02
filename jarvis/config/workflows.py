"""
config/workflows.py

Phase 4 -- Personal workflow definitions.

A workflow is a named sequence of actions executed one after another.
Each action is a dict with "intent" and "entities" keys -- exactly the
shape the ActionExecutor already understands.

How to add your own workflow:
    1. Pick a name (what you'll say to trigger it).
    2. Add a list of action steps under that name.
    3. No code changes needed anywhere else.

Trigger examples:
    "start coding session"   -> runs "coding session" workflow
    "morning routine"        -> runs "morning routine" workflow
    "chill mode"             -> runs "chill mode" workflow

Intent values must match constants in core/command.py.
Entity keys must match what the action handlers expect.
"""

WORKFLOWS: dict[str, list[dict]] = {

    # -- Coding Session --------------------------------------------------------
    # Opens browser, navigates to GitHub, plays focus music.
    "coding session": [
        {
            "intent":   "OPEN_APP",
            "entities": {"app_name": "chrome"},
            "label":    "Opening Chrome...",
        },
        {
            "intent":   "OPEN_WEBSITE",
            "entities": {"website": "github"},
            "label":    "Navigating to GitHub...",
        },
        {
            "intent":   "PLAY_MEDIA",
            "entities": {"song_name": "lofi hip hop focus music"},
            "label":    "Playing focus music...",
        },
    ],

    # -- Morning Routine -------------------------------------------------------
    # Opens Gmail, searches today's news, plays morning music.
    "morning routine": [
        {
            "intent":   "OPEN_WEBSITE",
            "entities": {"website": "gmail"},
            "label":    "Opening Gmail...",
        },
        {
            "intent":   "SEARCH_WEB",
            "entities": {"query": "today's top news India"},
            "label":    "Searching today's news...",
        },
        {
            "intent":   "PLAY_MEDIA",
            "entities": {"song_name": "good morning music energetic"},
            "label":    "Playing morning music...",
        },
    ],

    # -- Chill Mode ------------------------------------------------------------
    # Opens YouTube and plays relaxing music.
    "chill mode": [
        {
            "intent":   "OPEN_WEBSITE",
            "entities": {"website": "youtube"},
            "label":    "Opening YouTube...",
        },
        {
            "intent":   "PLAY_MEDIA",
            "entities": {"song_name": "lofi chill beats"},
            "label":    "Playing chill music...",
        },
    ],

    # -- Study Session ---------------------------------------------------------
    # Opens useful study resources and plays focus music.
    "study session": [
        {
            "intent":   "OPEN_WEBSITE",
            "entities": {"website": "wikipedia"},
            "label":    "Opening Wikipedia...",
        },
        {
            "intent":   "OPEN_WEBSITE",
            "entities": {"website": "stackoverflow"},
            "label":    "Opening Stack Overflow...",
        },
        {
            "intent":   "PLAY_MEDIA",
            "entities": {"song_name": "study music concentration"},
            "label":    "Playing study music...",
        },
    ],

    # -- Entertainment Mode ---------------------------------------------------
    # Quick entertainment setup.
    "entertainment mode": [
        {
            "intent":   "OPEN_WEBSITE",
            "entities": {"website": "youtube"},
            "label":    "Opening YouTube...",
        },
        {
            "intent":   "PLAY_MEDIA",
            "entities": {"song_name": "trending songs 2025"},
            "label":    "Playing trending music...",
        },
    ],

    # -- Add your own workflows below -----------------------------------------
    # Template:
    # "my workflow name": [
    #     { "intent": "OPEN_APP",     "entities": {"app_name": "notepad"},   "label": "Opening Notepad..." },
    #     { "intent": "OPEN_WEBSITE", "entities": {"website": "github"},      "label": "Opening GitHub..." },
    #     { "intent": "PLAY_MEDIA",   "entities": {"song_name": "my music"},  "label": "Playing music..." },
    # ],
}


# -- Workflow name aliases -----------------------------------------------------
# Maps alternate phrases to canonical workflow names.
# Allows: "start coding" -> "coding session"

WORKFLOW_ALIASES: dict[str, str] = {
    "coding":               "coding session",
    "start coding":         "coding session",
    "code session":         "coding session",
    "dev mode":             "coding session",
    "morning":              "morning routine",
    "start my day":         "morning routine",
    "good morning":         "morning routine",
    "chill":                "chill mode",
    "relax":                "chill mode",
    "relaxation mode":      "chill mode",
    "study":                "study session",
    "start studying":       "study session",
    "focus mode":           "study session",
    "entertainment":        "entertainment mode",
    "fun mode":             "entertainment mode",
    "watch something":      "entertainment mode",
}
