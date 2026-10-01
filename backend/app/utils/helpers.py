import math
from datetime import datetime, timezone


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def as_utc(dt: datetime | None) -> datetime | None:
    """SQLite returns naive datetimes; treat them as UTC."""
    if dt is None:
        return None
    return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)


def time_ago(dt: datetime | None) -> str:
    dt = as_utc(dt)
    if dt is None:
        return "-"
    secs = max(0, int((utcnow() - dt).total_seconds()))
    if secs < 60:
        return "just now"
    if secs < 3600:
        return f"{secs // 60} min ago"
    if secs < 86400:
        return f"{secs // 3600} h ago"
    return f"{secs // 86400} d ago"


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def eta_minutes(distance_km: float) -> int:
    """Rough ambulance ETA in city traffic (matches the frontend's 2.5 min/km)."""
    return max(1, round(distance_km * 2.5))


def ref_id(prefix: str, offset: int, pk: int) -> str:
    return f"{prefix}-{offset + pk}"


def parse_ref(value: str | int, prefix: str, offset: int) -> int | None:
    """'REF-1042' -> 42 ; '42' -> 42 ; invalid -> None."""
    s = str(value).strip().upper()
    if s.startswith(prefix + "-"):
        s = s[len(prefix) + 1:]
        return int(s) - offset if s.isdigit() else None
    return int(s) if s.isdigit() else None
