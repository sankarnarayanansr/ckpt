from datetime import datetime, timezone


def human_size(n: int) -> str:
    """Convert bytes to human-readable string."""
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024
    return f"{n:.1f} PB"


def human_date(iso: str) -> str:
    """Convert ISO date to readable local time."""
    dt = datetime.fromisoformat(iso)
    return dt.strftime("%Y-%m-%d %H:%M")


def short_id(full_id: str) -> str:
    return full_id[:7]


def elapsed(seconds: float) -> str:
    if seconds < 1:
        return f"{seconds*1000:.0f}ms"
    return f"{seconds:.1f}s"
