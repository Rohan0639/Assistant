"""
config/shell_commands.py

Phase 7 -- Whitelisted shell commands for RUN_COMMAND intent.

JARVIS will ONLY run commands defined in this dict.
This prevents accidental (or malicious) arbitrary code execution.

How to add your own:
    "my build":  ["cmd", "/c", "cd C:\\MyProject && npm run build"],
    "start server": ["python", "server.py"],

Keys are what you say to JARVIS (fuzzy matched).
Values are the exact subprocess args list to execute.
"""

# ── Your personal command shortcuts ──────────────────────────────────────────
# Edit this freely to add your own scripts and commands.

SHELL_COMMANDS: dict[str, list[str]] = {
    # System utilities
    "disk cleanup":     ["cleanmgr"],
    "task manager":     ["taskmgr"],
    "device manager":   ["devmgmt.msc"],
    "system info":      ["msinfo32"],
    "event viewer":     ["eventvwr"],
    "services":         ["services.msc"],
    "registry":         ["regedit"],
    "control panel":    ["control"],
    "network settings": ["ncpa.cpl"],
    "sound settings":   ["mmsys.cpl"],
    "display settings": ["desk.cpl"],

    # Developer tools
    "ipconfig":         ["cmd", "/c", "ipconfig"],
    "netstat":          ["cmd", "/c", "netstat", "-an"],
    "ping google":      ["cmd", "/c", "ping", "-n", "4", "google.com"],
    "flush dns":        ["cmd", "/c", "ipconfig", "/flushdns"],
    "python version":   ["python", "--version"],
    "node version":     ["node", "--version"],
    "npm version":      ["npm", "--version"],
    "git status":       ["cmd", "/c", "git", "status"],

    # Power / display
    "empty recycle bin": ["cmd", "/c", "rd /s /q %systemdrive%\\$Recycle.Bin"],
}
