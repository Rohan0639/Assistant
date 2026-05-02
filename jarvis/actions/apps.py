"""
actions/apps.py

Handles OPEN_APP intent.

Uses Python's subprocess module to launch desktop applications.
App name -> executable path mapping lives in config/apps.py.

Phase 2 addition:
    Multi-tier fuzzy lookup so "chrom" still finds "chrome",
    "calc" still finds "calculator", etc. No external libraries needed.

Lookup tiers (in priority order):
    Tier 1: Exact match          "chrome"        -> chrome.exe
    Tier 2: Starts-with          "chrom"         -> chrome.exe
    Tier 3: Input inside key     "google"        -> google chrome -> chrome.exe
    Tier 4: Key inside input     "note"          -> notepad -> notepad.exe

Windows note:
    subprocess.Popen() launches the process independently. The assistant
    does not wait for the app to close.
"""

import subprocess
import os
import shutil

from jarvis.config.apps import APP_REGISTRY, is_store_app


def _fuzzy_lookup(app_name: str) -> tuple[str | None, str | None]:
    """
    Multi-tier fuzzy lookup for an app name in the registry.

    Args:
        app_name: Normalized (lowercase) app name from user input.

    Returns:
        (matched_key, exe_path) if found, or (None, None) if not.
    """
    key = app_name.lower().strip()

    # Tier 1: Exact match
    if key in APP_REGISTRY:
        return key, APP_REGISTRY[key]

    # Tier 2: Registry key starts with user input
    # "chrom" -> finds "chrome"
    for reg_key, path in APP_REGISTRY.items():
        if reg_key.startswith(key):
            return reg_key, path

    # Tier 3: User input is contained in a registry key
    # "google" -> matches inside "google chrome"
    for reg_key, path in APP_REGISTRY.items():
        if key in reg_key:
            return reg_key, path

    # Tier 4: A registry key is contained in user input
    # "open the chrome browser" -> "chrome" found inside input
    for reg_key, path in APP_REGISTRY.items():
        if reg_key in key:
            return reg_key, path

    return None, None


def _is_available(exe_path: str) -> bool:
    """Check if an executable exists — also accepts Store app URIs."""
    if is_store_app(exe_path):
        return True   # Shell URIs always "available" — Windows handles it
    if os.path.isabs(exe_path):
        return os.path.exists(exe_path)
    return shutil.which(exe_path) is not None


def open_app(app_name: str) -> tuple[bool, str]:
    """
    Launch a desktop application by name.

    Phase 2: Uses fuzzy lookup so partial/typo names still work.

    Args:
        app_name: What the user said (e.g. "chrome", "chrom", "vs code")

    Returns:
        (success, response_message)
    """
    if not app_name:
        return False, "Which app would you like me to open?"

    matched_key, exe_path = _fuzzy_lookup(app_name)

    if not matched_key:
        known = ", ".join(sorted(APP_REGISTRY.keys()))
        return False, (
            f"I don't know how to open '{app_name}'. "
            f"Apps I know: {known}."
        )

    if not _is_available(exe_path):
        return False, (
            f"Found '{matched_key}' but the file doesn't exist at: {exe_path}. "
            f"Please update config/apps.py with the correct path."
        )

    try:
        if is_store_app(exe_path):
            # Launch Store apps / URI schemes via Windows shell
            subprocess.Popen(["explorer.exe", exe_path])
        else:
            subprocess.Popen([exe_path])
        display_name = matched_key.title()
        return True, f"Opening {display_name}..."
    except Exception as e:
        return False, f"Failed to open '{matched_key}': {e}"
