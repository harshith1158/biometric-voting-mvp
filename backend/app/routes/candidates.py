from flask import Blueprint, jsonify
from app.models import Candidate
from sqlalchemy import desc

bp = Blueprint("candidates", __name__, url_prefix="/api")


@bp.route("/candidates", methods=["GET"])
def list_candidates():
    """
    Retrieve list of candidates.
    ---
    tags:
      - Voting Booth
    summary: List all candidates
    description: >
      Retrieve all registered candidates with their party, name, and constituency.
      NOTA (None of the Above) always appears last in the list.
    responses:
      200:
        description: List of candidates
        schema:
          type: object
          properties:
            candidates:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: integer
                    example: 1
                  name:
                    type: string
                    example: "Arjun Mehta"
                  party:
                    type: string
                    example: "BJP"
                  state:
                    type: string
                    example: "Hyderabad Central"
    """
    # Query all candidates, excluding NOTA
    candidates = Candidate.query.filter(Candidate.candidate_name != "NOTA").all()
    
    # Query NOTA separately if it exists
    nota = Candidate.query.filter_by(candidate_name="NOTA").first()
    
    # Build response with regular candidates first, then NOTA
    result = []
    for c in candidates:
        result.append({
            "id": c.id,
            "name": c.candidate_name,
            "party": c.party,
            "state": c.constituency
        })
    
    # Add NOTA at the end if it exists
    if nota:
        result.append({
            "id": nota.id,
            "name": nota.candidate_name,
            "party": nota.party,
            "state": nota.constituency
        })
    
    return jsonify({
        "candidates": result
    }), 200
