"""
Seed data initialization for Sprint 3 voting booth.
"""

from app.models import Candidate
from app.db import db


def seed_candidates():
    """Initialize candidate data."""
    candidates_data = [
        {"party": "BJP", "candidate_name": "Arjun Mehta", "constituency": "Hyderabad Central"},
        {"party": "INC", "candidate_name": "Rahul Sharma", "constituency": "Hyderabad Central"},
        {"party": "AAP", "candidate_name": "Priya Nair", "constituency": "Hyderabad Central"},
        {"party": "IND", "candidate_name": "Vikram Singh", "constituency": "Hyderabad Central"},
        {"party": "TVK", "candidate_name": "Joseph Vijay", "constituency": "Hyderabad Central"},
        {"party": "Independent", "candidate_name": "NOTA", "constituency": "National"},  # NOTA appears last
    ]
    
    # Check if candidates already exist
    if Candidate.query.first() is not None:
        return  # Already seeded
    
    for data in candidates_data:
        candidate = Candidate(
            party=data["party"],
            candidate_name=data["candidate_name"],
            constituency=data["constituency"]
        )
        db.session.add(candidate)
    
    db.session.commit()
