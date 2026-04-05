"""
Seed data initialization for Sprint 3 voting booth.
"""

from app.models import Candidate
from app.db import db


def seed_candidates():
    """Initialize candidate data."""
    candidates = [
        {"name": "Narendra Modi", "party": "BJP", "state": "Telangana"},
        {"name": "Rahul Gandhi", "party": "INC", "state": "Telangana"},
        {"name": "Revanth Reddy", "party": "TDP", "state": "Telangana"},
        {"name": "Stalin", "party": "DMK", "state": "Telangana"},
        {"name": "Joseph Vijay", "party": "TVK", "state": "Telangana"},
    ]

    existing_keys = {
        (candidate.party, candidate.candidate_name, candidate.constituency)
        for candidate in Candidate.query.all()
    }

    seeded_any = False
    for data in candidates:
        candidate_key = (data["party"], data["name"], data["state"])
        if candidate_key in existing_keys:
            continue

        candidate = Candidate(
            party=data["party"],
            candidate_name=data["name"],
            constituency=data["state"]
        )
        db.session.add(candidate)
        seeded_any = True

    if seeded_any:
        db.session.commit()
