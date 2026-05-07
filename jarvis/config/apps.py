"""
config/apps.py

App name -> executable path mapping for Windows 11.

How to extend:
    Add a new entry to APP_REGISTRY with:
      key   = what the user might say (lowercase, no spaces preferred)
      value = full path to the .exe, OR just the .exe name if it is in PATH

Design notes:
    - Keys cover common aliases users might say.
      ("vs code", "vscode", "code" all map to the same exe)
    - Values use raw strings (r"...") to handle Windows backslashes safely.
    - If an app is in system PATH, just the exe name is enough.
    - Windows Store apps use the "shell:AppsFolder\\<PackageFamilyName>!App" protocol.
"""

import os

_USER = os.path.expanduser("~")

APP_REGISTRY: dict[str, str] = {

    # -- Browsers --------------------------------------------------------------
    "chrome":               r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "google chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "browser":              r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    "edge":                 r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "microsoft edge":       r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

    # -- Code Editors ----------------------------------------------------------
    "vs code":              rf"{_USER}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "vscode":               rf"{_USER}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "code":                 rf"{_USER}\AppData\Local\Programs\Microsoft VS Code\Code.exe",
    "visual studio code":   rf"{_USER}\AppData\Local\Programs\Microsoft VS Code\Code.exe",

    # -- Social & Communication (Windows Store apps) ---------------------------
    # These are launched via Windows shell protocol
    "instagram":            "shell:AppsFolder\\Facebook.InstagramBeta_8xx8rvfyw5nnt!App",
    "whatsapp":             "shell:AppsFolder\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm!App",
    "snapchat":             "shell:AppsFolder\\www.snapchat.com-42CD23B2_7yxfaf5zmzrp4!App",

    # -- Music & Media ---------------------------------------------------------
    "spotify":              rf"{_USER}\AppData\Roaming\Spotify\Spotify.exe",

    # -- Productivity ----------------------------------------------------------
    "word":                 r"C:\Program Files\Microsoft Office\root\Office16\WINWORD.EXE",
    "excel":                r"C:\Program Files\Microsoft Office\root\Office16\EXCEL.EXE",
    "powerpoint":           r"C:\Program Files\Microsoft Office\root\Office16\POWERPNT.EXE",
    "onenote":              r"C:\Program Files\Microsoft Office\root\Office16\ONENOTE.EXE",
    "outlook":              r"C:\Program Files\Microsoft Office\root\Office16\OUTLOOK.EXE",

    # -- System apps (always available on Windows) -----------------------------
    "notepad":              "notepad.exe",
    "calculator":           "calc.exe",
    "calc":                 "calc.exe",
    "file explorer":        "explorer.exe",
    "explorer":             "explorer.exe",
    "task manager":         "taskmgr.exe",
    "taskmgr":              "taskmgr.exe",
    "paint":                "mspaint.exe",
    "mspaint":              "mspaint.exe",
    "cmd":                  "cmd.exe",
    "command prompt":       "cmd.exe",
    "terminal":             "wt.exe",               # Windows Terminal
    "windows terminal":     "wt.exe",
    "powershell":           "powershell.exe",
    "snipping tool":        "SnippingTool.exe",
    "screenshot":           "SnippingTool.exe",
    "settings":             "ms-settings:",          # Opens Windows Settings
    "control panel":        "control.exe",
    "registry":             "regedit.exe",
    "device manager":       "devmgmt.msc",

    # -- Development -----------------------------------------------------------
    "git bash":             r"C:\Program Files\Git\git-bash.exe",
    "anaconda":             rf"{_USER}\anaconda3\Scripts\jupyter-notebook.exe",
    "jupyter":              rf"{_USER}\anaconda3\Scripts\jupyter-notebook.exe",

}


# ── Store app launcher helper ─────────────────────────────────────────────────

def is_store_app(exe_path: str) -> bool:
    """Return True if this entry should be launched via Windows shell."""
    return exe_path.startswith("shell:") or exe_path.startswith("ms-")


# -- Website shortcuts --------------------------------------------------------
# Used by OPEN_WEBSITE intent.
# Key = what user says, Value = full URL

WEBSITE_REGISTRY: dict[str, str] = {
    "youtube":          "https://www.youtube.com",
    "google":           "https://www.google.com",
    "github":           "https://www.github.com",
    "gmail":            "https://mail.google.com",
    "google mail":      "https://mail.google.com",
    "instagram":        "https://www.instagram.com",    # fallback if app not installed
    "whatsapp":         "https://web.whatsapp.com",
    "whatsapp web":     "https://web.whatsapp.com",
    "twitter":          "https://www.twitter.com",
    "x":                "https://www.twitter.com",
    "reddit":           "https://www.reddit.com",
    "stackoverflow":    "https://stackoverflow.com",
    "stack overflow":   "https://stackoverflow.com",
    "linkedin":         "https://www.linkedin.com",
    "netflix":          "https://www.netflix.com",
    "amazon":           "https://www.amazon.in",
    "spotify":          "https://open.spotify.com",
    "wikipedia":        "https://www.wikipedia.org",
    "chatgpt":          "https://chat.openai.com",
    "hotstar":          "https://www.hotstar.com",
    "jio hotstar":      "https://www.hotstar.com",
    "figma":            "https://www.figma.com",
    "notion":           "https://www.notion.so",
}
