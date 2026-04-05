import hashlib
from difflib import SequenceMatcher


def normalize_template(template: str) -> str:
    raw = (template or "").strip()
    if not raw:
        return ""

    # Keep only alphanumeric characters to reduce formatting noise.
    cleaned = "".join(ch for ch in raw if ch.isalnum())
    if not cleaned:
        return ""

    # Use a middle window because many RD payloads vary near the edges.
    if len(cleaned) <= 240:
        return cleaned[:120]

    mid = len(cleaned) // 2
    start = max(0, mid - 60)
    end = start + 120
    return cleaned[start:end]


def normalized_hash(template: str) -> str:
    normalized = normalize_template(template)
    if not normalized:
        return ""
    return hashlib.sha256(normalized.encode()).hexdigest()


def is_match(stored_template: str, incoming_template: str, threshold: float = 0.88) -> tuple[bool, float]:
    stored = normalize_template(stored_template)
    incoming = normalize_template(incoming_template)

    if not stored or not incoming:
        return False, 0.0

    if stored == incoming:
        return True, 1.0

    full_ratio = SequenceMatcher(None, stored, incoming).ratio()
    left_ratio = SequenceMatcher(None, stored[:60], incoming[:60]).ratio()
    right_ratio = SequenceMatcher(None, stored[-60:], incoming[-60:]).ratio()
    score = max(full_ratio, (left_ratio + right_ratio) / 2.0)

    return score >= threshold, score
