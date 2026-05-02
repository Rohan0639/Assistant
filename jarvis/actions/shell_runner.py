"""
actions/shell_runner.py

Phase 7 -- Safe shell command execution.

Handles RUN_COMMAND intent.

SECURITY MODEL:
    JARVIS will ONLY run commands explicitly listed in config/shell_commands.py.
    No arbitrary command execution is allowed — fuzzy matching finds the
    closest safe match from the whitelist.

Output handling:
    - Quick commands (ipconfig, ping) capture and display output in JARVIS
    - GUI commands (task manager, control panel) launch independently
"""

import subprocess
import logging

from jarvis.config.shell_commands import SHELL_COMMANDS

logger = logging.getLogger(__name__)

# Commands that produce terminal output worth showing
_CAPTURE_OUTPUT_COMMANDS = {
    "ipconfig", "netstat", "ping google", "flush dns",
    "python version", "node version", "npm version", "git status",
}


def _fuzzy_lookup(command_name: str) -> tuple[str | None, list | None]:
    """Find the closest matching command from the whitelist."""
    key = command_name.lower().strip()

    if key in SHELL_COMMANDS:
        return key, SHELL_COMMANDS[key]

    # Starts-with
    for k, v in SHELL_COMMANDS.items():
        if k.startswith(key) or key.startswith(k):
            return k, v

    # Substring
    for k, v in SHELL_COMMANDS.items():
        if key in k or k in key:
            return k, v

    return None, None


def run(command_name: str) -> tuple[bool, str]:
    """
    Run a whitelisted shell command by name.

    Args:
        command_name: What the user said (fuzzy matched to SHELL_COMMANDS).

    Returns:
        (success, response_message)
    """
    if not command_name:
        known = ", ".join(SHELL_COMMANDS.keys())
        return False, f"Which command? I know: {known}."

    matched_key, args = _fuzzy_lookup(command_name)

    if not matched_key:
        known = ", ".join(SHELL_COMMANDS.keys())
        return False, (
            f"'{command_name}' isn't in my command list. "
            f"Add it to config/shell_commands.py. Known: {known}."
        )

    try:
        capture = matched_key in _CAPTURE_OUTPUT_COMMANDS

        if capture:
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=15,
                shell=False,
            )
            output = (result.stdout or result.stderr or "").strip()
            output = output[:500] + "..." if len(output) > 500 else output
            if output:
                return True, f"Ran '{matched_key}':\n{output}"
            return True, f"Ran '{matched_key}' successfully."
        else:
            subprocess.Popen(args, shell=False)
            return True, f"Launched '{matched_key}'."

    except subprocess.TimeoutExpired:
        return False, f"'{matched_key}' timed out."
    except FileNotFoundError:
        return False, f"Command not found for '{matched_key}'. Check config/shell_commands.py."
    except Exception as e:
        logger.error("shell_runner error for '%s': %s", matched_key, e)
        return False, f"Error running '{matched_key}': {e}"
