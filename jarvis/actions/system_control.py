"""
actions/system_control.py

Phase 7 -- OS-level system controls.

Handles SYSTEM_CONTROL intent. Supports:
    Volume:  volume_up, volume_down, mute, unmute, set_volume
    Power:   sleep, shutdown, restart, cancel_shutdown
    Screen:  lock, brightness_up, brightness_down

All implemented via PowerShell or Windows APIs — no extra libraries needed.
"""

import subprocess
import logging

logger = logging.getLogger(__name__)


# ── Volume control (via PowerShell + WScript) ──────────────────────────────

def _send_key(key_code: int, times: int = 1) -> None:
    """Send a virtual key press via PowerShell WScript.Shell."""
    script = (
        f'$wsh = New-Object -ComObject WScript.Shell; '
        f'for ($i=0; $i -lt {times}; $i++) {{ $wsh.SendKeys([char]{key_code}) }}'
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
        capture_output=True
    )


def volume_up(steps: int = 5) -> tuple[bool, str]:
    """Increase system volume."""
    _send_key(175, steps)   # VK_VOLUME_UP
    return True, f"Volume increased by {steps} steps."


def volume_down(steps: int = 5) -> tuple[bool, str]:
    """Decrease system volume."""
    _send_key(174, steps)   # VK_VOLUME_DOWN
    return True, f"Volume decreased by {steps} steps."


def mute() -> tuple[bool, str]:
    """Mute system audio."""
    _send_key(173)           # VK_VOLUME_MUTE
    return True, "Audio muted."


def unmute() -> tuple[bool, str]:
    """Unmute system audio (same key toggles)."""
    _send_key(173)
    return True, "Audio unmuted."


def set_volume(level: int) -> tuple[bool, str]:
    """
    Set volume to an absolute level (0-100).
    Uses a robust fallback: decrease volume to 0 by pressing VolDown 50 times,
    then increase to the desired level by pressing VolUp (level // 2) times.
    """
    level = max(0, min(100, int(level)))
    
    try:
        # Volume down 50 times to guarantee reaching 0 (each press is 2%)
        _send_key(174, 50)
        
        # Volume up to target level
        steps_up = level // 2
        if steps_up > 0:
            _send_key(175, steps_up)
            
        return True, f"Volume set to {level}%."
    except Exception as e:
        logger.error("set_volume error: %s", e)
        return False, "Couldn't set exact volume. Try 'volume up' or 'volume down'."

# ── Brightness controls ───────────────────────────────────────────────────────

def set_brightness(level: int) -> tuple[bool, str]:
    """Set the screen brightness (0-100) using PowerShell WMI."""
    level = max(0, min(100, int(level)))
    script = f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods).WmiSetBrightness(1, {level})"
    try:
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script], check=True, capture_output=True)
        return True, f"Brightness set to {level}%."
    except Exception as e:
        logger.error("set_brightness error: %s", e)
        return False, "I couldn't adjust the brightness on this display."


# ── Power controls ────────────────────────────────────────────────────────────

def sleep_pc() -> tuple[bool, str]:
    """Put the PC to sleep."""
    try:
        subprocess.Popen(
            ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"]
        )
        return True, "Going to sleep. Goodnight!"
    except Exception as e:
        return False, f"Couldn't sleep: {e}"


def shutdown_pc(delay: int = 10) -> tuple[bool, str]:
    """Shutdown the PC after a delay (seconds)."""
    try:
        subprocess.run(["shutdown", "/s", "/t", str(delay)], check=True)
        return True, f"Shutting down in {delay} seconds. Goodbye!"
    except Exception as e:
        return False, f"Couldn't shutdown: {e}"


def restart_pc(delay: int = 10) -> tuple[bool, str]:
    """Restart the PC after a delay (seconds)."""
    try:
        subprocess.run(["shutdown", "/r", "/t", str(delay)], check=True)
        return True, f"Restarting in {delay} seconds."
    except Exception as e:
        return False, f"Couldn't restart: {e}"


def cancel_shutdown() -> tuple[bool, str]:
    """Cancel a pending shutdown or restart."""
    try:
        subprocess.run(["shutdown", "/a"], check=True)
        return True, "Shutdown cancelled."
    except Exception as e:
        return False, f"No pending shutdown to cancel (or error: {e})"


def lock_screen() -> tuple[bool, str]:
    """Lock the Windows screen."""
    try:
        subprocess.Popen(["rundll32.exe", "user32.dll,LockWorkStation"])
        return True, "Screen locked."
    except Exception as e:
        return False, f"Couldn't lock screen: {e}"


# ── Dispatcher ────────────────────────────────────────────────────────────────

def handle(action: str, value: str = "") -> tuple[bool, str]:
    """
    Route SYSTEM_CONTROL intent to the right function.

    Args:
        action: Action string from the AI parser entity.
        value:  Optional numeric value (e.g. volume level).

    Examples:
        handle("volume_up")          -> increases volume
        handle("set_volume", "60")   -> sets to 60%
        handle("shutdown")           -> schedules shutdown
        handle("lock")               -> locks screen
    """
    action = action.lower().strip()

    if action == "volume_up":
        return volume_up()
    elif action == "volume_down":
        return volume_down()
    elif action in ("mute", "silence"):
        return mute()
    elif action == "unmute":
        return unmute()
    elif action == "set_volume":
        try:
            lvl = int("".join(c for c in value if c.isdigit()) or "50")
            return set_volume(lvl)
        except ValueError:
            return False, "Please specify a volume level like 'set volume to 60'."
    elif action in ("sleep", "suspend"):
        return sleep_pc()
    elif action in ("shutdown", "shut down", "turn off", "power off"):
        return shutdown_pc()
    elif action in ("restart", "reboot"):
        return restart_pc()
    elif action == "cancel_shutdown":
        return cancel_shutdown()
    elif action in ("lock", "lock_screen", "lock screen"):
        return lock_screen()
    elif action == "set_brightness":
        try:
            lvl = int("".join(c for c in value if c.isdigit()) or "50")
            return set_brightness(lvl)
        except ValueError:
            return False, "Please specify a brightness level like 'set brightness to 70'."
    else:
        return False, (
            f"I don't know the system action '{action}'. "
            "Try: volume up/down, mute, set_brightness, sleep, shutdown, restart, lock."
        )
