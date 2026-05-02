"""
actions/file_actions.py

Phase 7 -- File and folder navigation.

Handles FILE_ACTION intent. Supports:
    - Open named folders (Downloads, Desktop, Documents, Pictures, etc.)
    - Open files by path or name
    - Open the project folder
    - Open any custom path
"""

import os
import subprocess
import logging

logger = logging.getLogger(__name__)

# ── Common folder shortcuts ───────────────────────────────────────────────────

_HOME = os.path.expanduser("~")

FOLDER_SHORTCUTS = {
    "desktop":      os.path.join(_HOME, "Desktop"),
    "downloads":    os.path.join(_HOME, "Downloads"),
    "documents":    os.path.join(_HOME, "Documents"),
    "pictures":     os.path.join(_HOME, "Pictures"),
    "music":        os.path.join(_HOME, "Music"),
    "videos":       os.path.join(_HOME, "Videos"),
    "home":         _HOME,
    "user":         _HOME,
    "temp":         os.environ.get("TEMP", "C:\\Windows\\Temp"),
    "appdata":      os.environ.get("APPDATA", ""),
    "localappdata": os.environ.get("LOCALAPPDATA", ""),
    "windows":      "C:\\Windows",
    "program files": "C:\\Program Files",
    "system32":     "C:\\Windows\\System32",
    "c drive":      "C:\\",
    "c:":           "C:\\",
}


def _fuzzy_folder(name: str) -> str | None:
    """Find a folder path from a fuzzy name match."""
    key = name.lower().strip()
    # Exact match
    if key in FOLDER_SHORTCUTS:
        return FOLDER_SHORTCUTS[key]
    # Starts-with match
    for k, v in FOLDER_SHORTCUTS.items():
        if k.startswith(key) or key.startswith(k):
            return v
    # Substring match
    for k, v in FOLDER_SHORTCUTS.items():
        if key in k or k in key:
            return v
    return None


def open_folder(folder_name: str) -> tuple[bool, str]:
    """
    Open a folder in Windows Explorer by name or path.

    Args:
        folder_name: Common name (e.g. "downloads") or absolute path.

    Returns:
        (success, response_message)
    """
    if not folder_name:
        return False, "Which folder would you like to open?"

    # Direct absolute path check first
    if os.path.isabs(folder_name) and os.path.isdir(folder_name):
        subprocess.Popen(["explorer", folder_name])
        return True, f"Opening {folder_name}."

    # Fuzzy name lookup
    path = _fuzzy_folder(folder_name)
    if path and os.path.isdir(path):
        subprocess.Popen(["explorer", path])
        return True, f"Opening {folder_name.title()} folder."

    # Try treating it as a relative path from Desktop or home
    for base in [os.path.join(_HOME, "Desktop"), _HOME]:
        candidate = os.path.join(base, folder_name)
        if os.path.isdir(candidate):
            subprocess.Popen(["explorer", candidate])
            return True, f"Opening {folder_name}."

    known = ", ".join(FOLDER_SHORTCUTS.keys())
    return False, f"Couldn't find folder '{folder_name}'. Known folders: {known}."


def open_file(file_path: str) -> tuple[bool, str]:
    """
    Open a file using its default application.

    Args:
        file_path: Absolute path or filename to search for.

    Returns:
        (success, response_message)
    """
    if not file_path:
        return False, "Which file would you like to open?"

    # Absolute path
    if os.path.isabs(file_path) and os.path.isfile(file_path):
        os.startfile(file_path)
        return True, f"Opening {os.path.basename(file_path)}."

    # Search in common locations
    search_dirs = [
        os.path.join(_HOME, "Desktop"),
        os.path.join(_HOME, "Downloads"),
        os.path.join(_HOME, "Documents"),
        _HOME,
    ]
    for directory in search_dirs:
        candidate = os.path.join(directory, file_path)
        if os.path.isfile(candidate):
            os.startfile(candidate)
            return True, f"Opening {file_path} from {os.path.basename(directory)}."

    return False, (
        f"Couldn't find file '{file_path}'. "
        "Try giving the full path or check the filename."
    )


def handle(action: str, target: str = "") -> tuple[bool, str]:
    """
    Route FILE_ACTION intent to the right function.

    Args:
        action: "open_folder" or "open_file"
        target: The folder/file name or path.
    """
    action = action.lower().strip()

    if action in ("open_folder", "folder", "explore"):
        return open_folder(target)
    elif action in ("open_file", "file"):
        return open_file(target)
    else:
        # Guess intent from target
        if os.path.isdir(target) or target.lower() in FOLDER_SHORTCUTS:
            return open_folder(target)
        return open_file(target)
