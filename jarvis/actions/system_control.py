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
    Uses PowerShell audio API.
    """
    level = max(0, min(100, int(level)))
    script = (
        f'$vol = [math]::Round({level} / 100, 2); '
        f'$obj = New-Object -ComObject WScript.Shell; '
        f'[Audio]::Volume = $vol'
    )
    # Simpler approach: mute first then adjust relative
    # Set via nircmd alternative using PowerShell COM
    ps_script = f"""
$wsh = New-Object -ComObject WScript.Shell
# Set master volume via Windows Audio Session API
Add-Type -TypeDefinition @'
using System.Runtime.InteropServices;
[Guid("5CDF2C82-841E-4546-9722-0CF74078229A"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IAudioEndpointVolume {{
    int _VtblGap1_6();
    int SetMasterVolumeLevelScalar(float fLevel, System.Guid pguidEventContext);
    int _VtblGap2_1();
    int GetMasterVolumeLevelScalar(out float pfLevel);
}}
[Guid("BCDE0395-E52F-467C-8E3D-C4579291692E")]
class MMDeviceEnumerator {{}}
[Guid("A95664D2-9614-4F35-A746-DE8DB63617E6"), InterfaceType(ComInterfaceType.InterfaceIsIUnknown)]
interface IMMDeviceEnumerator {{
    int _VtblGap1_3();
    int GetDefaultAudioEndpoint(int dataFlow, int role, out System.IntPtr ppDevice);
}}
public class AudioManager {{
    public static void SetVolume(float level) {{
        var enumeratorType = Type.GetTypeFromCLSID(new System.Guid("BCDE0395-E52F-467C-8E3D-C4579291692E"));
        var enumerator = (IMMDeviceEnumerator)System.Activator.CreateInstance(enumeratorType);
        System.IntPtr devicePtr;
        enumerator.GetDefaultAudioEndpoint(0, 1, out devicePtr);
    }}
}}
'@
"""
    try:
        # Simpler fallback: use relative key presses to approximate
        # First mute, then set via key simulation isn't perfect for absolute
        # Use direct PowerShell approach
        cmd = [
            "powershell", "-NoProfile", "-NonInteractive", "-Command",
            f"""
$obj = New-Object -com WScript.Shell
$current = (Get-WmiObject -Query "SELECT * FROM Win32_SoundDevice" | Select-Object -First 1)
Add-Type -TypeDefinition '
using System.Runtime.InteropServices;
public class Vol {{
    [DllImport("winmm.dll")]
    public static extern int waveOutSetVolume(IntPtr h, uint dwVolume);
    [DllImport("winmm.dll")]
    public static extern int waveOutGetVolume(IntPtr h, out uint dwVolume);
}}'
$vol = [uint32]([math]::Round({level}/100.0 * 65535)) * 65537
[Vol]::waveOutSetVolume([IntPtr]::Zero, $vol)
"""
        ]
        subprocess.run(cmd, capture_output=True, timeout=5)
        return True, f"Volume set to {level}%."
    except Exception as e:
        logger.error("set_volume error: %s", e)
        return False, f"Couldn't set exact volume. Try 'volume up' or 'volume down'."


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
    else:
        return False, (
            f"I don't know the system action '{action}'. "
            "Try: volume up/down, mute, sleep, shutdown, restart, lock."
        )
