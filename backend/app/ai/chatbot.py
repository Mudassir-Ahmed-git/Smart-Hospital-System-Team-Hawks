"""Rule-based healthcare assistant. Deterministic and grounded in live capacity data
(no hallucinated beds). Intent detection is keyword based, which is robust for a demo and
easy to swap for an LLM later: only `detect` needs replacing."""
import re

BED_KEYWORDS = [
    ("ICU", r"\bicu\b|intensive care|critical care"),
    ("Ventilator", r"ventilator|\bvent\b|breathing machine|oxygen support"),
    ("Operation Theater", r"operation theat|operating (room|theat)|\bot\b|surgery|surgical"),
    ("General", r"\bgeneral\b|\bward\b|normal bed|regular bed"),
    ("Emergency", r"emergency|\ber\b|trauma|accident"),
]
SEVERE = r"emergency|urgent|critical|asap|immediately|accident|heart attack|stroke|dying|now"


def detect(message: str) -> dict:
    t = message.lower()
    bed_type = next((b for b, pat in BED_KEYWORDS if re.search(pat, t)), None)
    if re.search(r"forecast|predict|tomorrow|next (day|week)|expect|trend", t):
        intent = "forecast"
    elif re.search(r"alert|overload|shortage|spike|warning|status of the network", t):
        intent = "alerts"
    elif re.search(r"nearest|closest|near me|nearby", t) and not bed_type:
        intent = "nearest"
    elif re.search(r"hello|hi\b|hey|help|what can you do", t) and not bed_type:
        intent = "greeting"
    elif bed_type or re.search(r"bed|hospital|admit|admission|capacity|available", t):
        intent = "availability"
    else:
        intent = "unknown"
    return {
        "intent": intent,
        "bed_type": bed_type or ("General" if intent == "availability" else None),
        "priority": "Critical" if re.search(SEVERE, t) else "Urgent",
    }


HELP_TEXT = ("I can find hospitals with free ICU, emergency, general or ventilator beds, tell you the nearest "
             "hospital, forecast tomorrow's demand, or list capacity alerts. Try: \"Need emergency ICU\".")


def reply_availability(bed_type: str, ranked: list[dict]) -> str:
    if not ranked:
        return (f"No hospital currently has a free {bed_type} bed. I'd suggest calling dispatch to arrange a "
                f"transfer, or asking again in a few minutes.")
    best = ranked[0]
    n = best["available"]
    text = (f"{n} {bed_type} bed{'s' if n != 1 else ''} available at {best['hospital']} "
            f"({best['distanceKm']} km away, ~{best['etaMinutes']} min).")
    if len(ranked) > 1:
        alt = ranked[1]
        text += f" Next best: {alt['hospital']} with {alt['available']} free ({alt['distanceKm']} km)."
    return text
