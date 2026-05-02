"""
actions/system_info.py

Phase 7 -- System information queries.

Handles SYSTEM_INFO intent. Reports:
    battery  -- charge level, charging status
    ram      -- total, used, free memory
    cpu      -- current CPU usage %
    disk     -- C: drive free/used space
    all      -- everything at once

Uses psutil (pip install psutil) for cross-platform hardware info.
"""

import logging

logger = logging.getLogger(__name__)


def _get_psutil():
    """Lazy import psutil with a friendly error if not installed."""
    try:
        import psutil
        return psutil
    except ImportError:
        return None


def get_battery() -> tuple[bool, str]:
    """Return battery status."""
    ps = _get_psutil()
    if not ps:
        return False, "psutil not installed. Run: pip install psutil"

    battery = ps.sensors_battery()
    if battery is None:
        return True, "No battery detected — you're on a desktop PC."

    pct     = battery.percent
    charging = battery.power_plugged

    if charging:
        status = "charging 🔌"
    elif pct > 20:
        status = "on battery 🔋"
    else:
        status = "LOW — plug in now! ⚠️"

    secs = battery.secsleft
    if secs and secs > 0 and not charging:
        h, m = divmod(secs // 60, 60)
        time_left = f" (~{h}h {m}m remaining)"
    else:
        time_left = ""

    return True, f"Battery: {pct:.0f}% {status}{time_left}."


def get_ram() -> tuple[bool, str]:
    """Return RAM usage."""
    ps = _get_psutil()
    if not ps:
        return False, "psutil not installed. Run: pip install psutil"

    mem = ps.virtual_memory()
    total_gb = mem.total / (1024 ** 3)
    used_gb  = mem.used  / (1024 ** 3)
    free_gb  = mem.available / (1024 ** 3)
    pct      = mem.percent

    return True, (
        f"RAM: {used_gb:.1f} GB used / {total_gb:.1f} GB total "
        f"({pct:.0f}% used, {free_gb:.1f} GB free)."
    )


def get_cpu() -> tuple[bool, str]:
    """Return CPU usage."""
    ps = _get_psutil()
    if not ps:
        return False, "psutil not installed. Run: pip install psutil"

    # interval=1 gives a 1-second average (more accurate)
    usage = ps.cpu_percent(interval=1)
    cores = ps.cpu_count(logical=True)
    freq  = ps.cpu_freq()

    freq_str = f" @ {freq.current:.0f} MHz" if freq else ""
    load = "🔴 High" if usage > 80 else ("🟡 Moderate" if usage > 40 else "🟢 Low")

    return True, f"CPU: {usage:.0f}% usage{freq_str} ({cores} cores) — {load}."


def get_disk() -> tuple[bool, str]:
    """Return disk usage for C: drive."""
    ps = _get_psutil()
    if not ps:
        return False, "psutil not installed. Run: pip install psutil"

    try:
        disk = ps.disk_usage("C:\\")
        total_gb = disk.total / (1024 ** 3)
        used_gb  = disk.used  / (1024 ** 3)
        free_gb  = disk.free  / (1024 ** 3)
        pct      = disk.percent

        return True, (
            f"Disk (C:): {used_gb:.1f} GB used / {total_gb:.1f} GB total "
            f"({pct:.0f}% full, {free_gb:.1f} GB free)."
        )
    except Exception as e:
        return False, f"Couldn't read disk info: {e}"


def get_all() -> tuple[bool, str]:
    """Return a full system snapshot."""
    lines = ["System Status:"]

    _, bat = get_battery()
    lines.append(f"  {bat}")

    _, ram = get_ram()
    lines.append(f"  {ram}")

    _, cpu = get_cpu()
    lines.append(f"  {cpu}")

    _, disk = get_disk()
    lines.append(f"  {disk}")

    return True, "\n".join(lines)


def handle(metric: str) -> tuple[bool, str]:
    """
    Route SYSTEM_INFO intent to the right reporter.

    Args:
        metric: "battery", "ram", "cpu", "disk", or "all"
    """
    metric = metric.lower().strip()

    if metric in ("battery", "charge", "power"):
        return get_battery()
    elif metric in ("ram", "memory", "ram usage"):
        return get_ram()
    elif metric in ("cpu", "processor", "cpu usage"):
        return get_cpu()
    elif metric in ("disk", "storage", "hard drive", "space"):
        return get_disk()
    elif metric in ("all", "everything", "status", "system"):
        return get_all()
    else:
        # Default to full status for unrecognised metrics
        return get_all()
