"""Hospital recommendation scoring (pure functions, no DB access).

score = 0.40*availability + 0.30*distance + 0.20*emergency_capability + 0.10*waiting_time
Each component is normalised to 0..1.
"""
from dataclasses import dataclass, field

WEIGHTS = {"availability": 0.40, "distance": 0.30, "capability": 0.20, "waiting": 0.10}
MINUTES_PER_PENDING_REQUEST = 4   # heuristic queue service time
BASE_WAIT_MINUTES = 5


@dataclass
class Candidate:
    hospital_id: int
    name: str
    area: str
    distance_km: float
    total: int                      # beds of the required type
    available: int                  # free beds of the required type
    emergency_status: str           # OPEN | BUSY | CLOSED
    emergency_beds_free: int
    critical_care_free: int         # free ICU + ventilator beds
    pending_requests: int           # queue for this bed type
    specialties: list[str] = field(default_factory=list)


def availability_score(c: Candidate) -> float:
    if c.available <= 0 or c.total <= 0:
        return 0.0
    # Absolute headroom matters: 1 free bed on a 4-bed unit is not "100% available".
    return min(1.0, c.available / max(3.0, 0.3 * c.total))


def distance_score(distance_km: float, max_km: float) -> float:
    return max(0.0, 1.0 - distance_km / max_km)


def capability_score(c: Candidate) -> float:
    score = {"OPEN": 0.6, "BUSY": 0.3}.get(c.emergency_status, 0.0)
    score += 0.2 if c.emergency_beds_free > 0 else 0.0
    score += 0.2 if c.critical_care_free > 0 else 0.0
    return score


def waiting_score(pending: int) -> float:
    return 1.0 / (1.0 + pending / 3.0)


def estimated_wait_minutes(pending: int) -> int:
    return BASE_WAIT_MINUTES + MINUTES_PER_PENDING_REQUEST * pending


def rank(candidates: list[Candidate], priority: str, max_km: float, specialty: str | None = None) -> list[dict]:
    """Return scored hospitals, best first. Hospitals with no free bed of the required type, and
    (for Critical patients) hospitals whose emergency department is CLOSED, are excluded."""
    results = []
    for c in candidates:
        if c.available <= 0:
            continue
        if priority == "Critical" and c.emergency_status == "CLOSED":
            continue
        parts = {
            "availability": availability_score(c),
            "distance": distance_score(c.distance_km, max_km),
            "capability": capability_score(c),
            "waiting": waiting_score(c.pending_requests),
        }
        total = sum(WEIGHTS[k] * v for k, v in parts.items())
        if specialty and any(specialty.lower() in s.lower() for s in c.specialties):
            total = min(1.0, total + 0.05)  # small tie-breaking bonus, doesn't override the spec'd weights
        results.append({"candidate": c, "score": round(total * 100, 1),
                        "breakdown": {k: round(v * 100, 1) for k, v in parts.items()}})
    results.sort(key=lambda r: (-r["score"], r["candidate"].distance_km))
    return results


def explain(entry: dict, bed_type: str, is_nearest: bool, is_most_beds: bool) -> str:
    c: Candidate = entry["candidate"]
    n = c.available
    if is_nearest and is_most_beds:
        lead = f"Nearest {bed_type} availability and most beds free ({n})"
    elif is_nearest:
        lead = f"Nearest {bed_type} availability ({n} free)"
    elif is_most_beds:
        lead = f"Most {bed_type} beds free ({n})"
    else:
        lead = f"Best overall balance for {bed_type} ({n} free)"
    return (f"{lead}, {c.distance_km:.1f} km away, emergency {c.emergency_status}, "
            f"est. wait {estimated_wait_minutes(c.pending_requests)} min")
