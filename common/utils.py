"""Shared utility helpers for the ModelAtlas pipeline."""

from datetime import datetime, timezone

_HUMAN_DATE_FORMATS = (
    "%b %d, %Y %I:%M %p",
    "%b %d, %Y",
)


def normalize_date(value) -> str | None:
    """Coerce any date representation to an ISO 8601 UTC string.

    Handles:
    - None / empty string → None
    - Unix timestamps (int/float) → ISO
    - Already ISO-like strings (YYYY-...) → pass through unchanged
    - Human-readable strings like "Oct 28, 2025 6:32 PM UTC" → ISO
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(int(value), tz=timezone.utc).isoformat()
        except (ValueError, OSError):
            return None
    s = str(value).strip()
    if not s:
        return None
    # Already ISO-like
    if len(s) >= 10 and s[4:5] == "-":
        return s
    # Strip trailing timezone label before strptime (UTC is implicit)
    s_clean = s.removesuffix(" UTC").strip()
    for fmt in _HUMAN_DATE_FORMATS:
        try:
            dt = datetime.strptime(s_clean, fmt)
            return dt.replace(tzinfo=timezone.utc).isoformat()
        except ValueError:
            continue
    return s
