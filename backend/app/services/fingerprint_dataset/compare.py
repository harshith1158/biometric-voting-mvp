from app.services.fingerprint_dataset.matcher import match_score
from app.services.fingerprint_dataset.storage import load_fp


def compare_voters(voter1_id, voter2_id):
    d1 = load_fp(voter1_id)
    d2 = load_fp(voter2_id)

    if d1 is None or d2 is None:
        return 0

    score = match_score(d1, d2)

    return score
