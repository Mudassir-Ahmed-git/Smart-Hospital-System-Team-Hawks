"""Normalisation of enum-like values. The frontend and the spec use slightly different
words (High/Urgent, ICU/ICU Bed, ...), so we accept both and store one canonical form."""
from fastapi import HTTPException

ROLES = ("patient", "hospital", "ambulance", "admin")
BED_TYPES = ("ICU", "General", "Emergency", "Ventilator", "Operation Theater")
BED_STATUSES = ("Available", "Occupied", "Reserved", "Cleaning")
PRIORITIES = ("Normal", "Urgent", "Critical")
PRIORITY_RANK = {"Critical": 0, "Urgent": 1, "Normal": 2}
EMERGENCY_STATUSES = ("OPEN", "BUSY", "CLOSED")
REFERRAL_STATUSES = ("Pending", "Accepted", "Rejected", "Completed", "Cancelled")
AMBULANCE_STEPS = ("Patient picked up", "En route to hospital", "Arrived at hospital", "Handover complete")
EMERGENCY_REQUEST_STATUSES = ("Pending", "Accepted", "Declined", "Admitted", "Completed")

_ROLE_ALIASES = {
    "patient": "patient",
    "hospital": "hospital", "hospital staff": "hospital", "hospital_staff": "hospital", "staff": "hospital",
    "ambulance": "ambulance", "ambulance coordinator": "ambulance", "ambulance_coordinator": "ambulance",
    "admin": "admin", "administrator": "admin",
}
_BED_ALIASES = {
    "icu": "ICU", "icu bed": "ICU",
    "general": "General", "general bed": "General", "ward": "General",
    "emergency": "Emergency", "er": "Emergency",
    "ventilator": "Ventilator", "vent": "Ventilator",
    "operation theater": "Operation Theater", "operation theatre": "Operation Theater",
    "operation_theater": "Operation Theater", "ot": "Operation Theater",
}
_PRIORITY_ALIASES = {"normal": "Normal", "urgent": "Urgent", "high": "Urgent", "critical": "Critical"}
_STATUS_ALIASES = {s.lower(): s for s in BED_STATUSES}
_STATUS_ALIASES.update({"free": "Available", "cleaning": "Cleaning"})


def _lookup(value, table: dict, what: str, allowed) -> str:
    key = str(value or "").strip().lower()
    if key in table:
        return table[key]
    raise ValueError(f"Invalid {what} '{value}'. Allowed: {', '.join(allowed)}")


def normalize_role(value) -> str:
    return _lookup(value, _ROLE_ALIASES, "role", ROLES)


def normalize_bed_type(value) -> str:
    return _lookup(value, _BED_ALIASES, "bed type", BED_TYPES)


def normalize_priority(value) -> str:
    return _lookup(value, _PRIORITY_ALIASES, "priority", PRIORITIES)


def normalize_bed_status(value) -> str:
    return _lookup(value, _STATUS_ALIASES, "bed status", BED_STATUSES)


def normalize_emergency_status(value) -> str:
    v = str(value or "").strip().upper()
    if v not in EMERGENCY_STATUSES:
        raise ValueError(f"Invalid emergency status '{value}'. Allowed: {', '.join(EMERGENCY_STATUSES)}")
    return v


def validate_coordinates(lat: float | None, lng: float | None) -> None:
    if lat is not None and not -90 <= lat <= 90:
        raise HTTPException(422, "latitude must be between -90 and 90")
    if lng is not None and not -180 <= lng <= 180:
        raise HTTPException(422, "longitude must be between -180 and 180")


def bed_prefix(bed_type: str) -> str:
    return {"ICU": "ICU", "General": "GEN", "Emergency": "EMR", "Ventilator": "VEN", "Operation Theater": "OT"}[bed_type]
