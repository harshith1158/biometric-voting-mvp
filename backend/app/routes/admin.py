"""
Admin-only endpoints:
  GET  /api/admin/election_status  — current election state
  POST /api/admin/declare_result   — close election & declare winner
  GET  /api/admin/verify_chain     — detailed blockchain integrity report
  GET  /api/admin/results          — live vote tally
"""
import logging
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from app.db import db
from app.models import Candidate, ElectionStatus, Vote, Voter
from app.services.hash_chain import verify_chain_detailed

bp = Blueprint("admin", __name__, url_prefix="/api/admin")
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _get_or_init_election() -> ElectionStatus:
    """Return the singleton ElectionStatus row, creating it if absent."""
    status = ElectionStatus.query.first()
    if not status:
        status = ElectionStatus(status="open")
        db.session.add(status)
        db.session.commit()
    return status


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@bp.route("/election_status", methods=["GET"])
def election_status():
    """
    Return current election status.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Election status
        schema:
          type: object
          properties:
            status:
              type: string
              example: "open"
            closed_at:
              type: string
              example: null
            winner_candidate_id:
              type: integer
              example: null
    """
    status = _get_or_init_election()
    return jsonify(
        {
            "status": status.status,
            "closed_at": status.closed_at.isoformat() if status.closed_at else None,
            "winner_candidate_id": status.winner_candidate_id,
        }
    ), 200


@bp.route("/declare_result", methods=["POST"])
def declare_result():
    """
    Declare election results and permanently close the election.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Election closed with winner declared
      400:
        description: Election already closed or no votes cast
    """
    status = _get_or_init_election()

    if status.status == "closed":
        logger.warning("[ADMIN] Declare result called but election already closed")
        return jsonify({"error": "Election already declared and closed"}), 400

    # Tally all votes
    results = (
        db.session.query(Vote.candidate_id, func.count(Vote.id).label("vote_count"))
        .group_by(Vote.candidate_id)
        .order_by(func.count(Vote.id).desc())
        .all()
    )

    if not results:
        return jsonify({"error": "No votes have been cast yet"}), 400

    winner_id = results[0].candidate_id
    winner = Candidate.query.get(winner_id)

    # Lock the election
    status.status = "closed"
    status.closed_at = datetime.utcnow()
    status.winner_candidate_id = winner_id
    db.session.commit()

    tally = []
    for r in results:
        candidate = Candidate.query.get(r.candidate_id)
        tally.append(
            {
                "candidate_id": r.candidate_id,
                "candidate_name": candidate.candidate_name if candidate else "Unknown",
                "party": candidate.party if candidate else "Unknown",
                "vote_count": r.vote_count,
            }
        )

    logger.info(
        "[ADMIN] Election declared closed. Winner: %s (ID %d)",
        winner.candidate_name if winner else "Unknown",
        winner_id,
    )

    return jsonify(
        {
            "status": "closed",
            "winner": {
                "candidate_id": winner_id,
                "candidate_name": winner.candidate_name if winner else "Unknown",
                "party": winner.party if winner else "Unknown",
            },
            "tally": tally,
        }
    ), 200


@bp.route("/verify_chain", methods=["GET"])
def admin_verify_chain():
    """
    Recompute all blockchain hashes and report any tampering.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Chain integrity report
        schema:
          type: object
          properties:
            valid:
              type: boolean
            total_blocks:
              type: integer
            tampered_count:
              type: integer
            tampered_blocks:
              type: array
    """
    report = verify_chain_detailed()

    if report["valid"]:
        logger.info("[ADMIN] Blockchain verified — no tampering detected (%d blocks)", report["total_blocks"])
    else:
        logger.warning(
            "[ADMIN] BLOCKCHAIN TAMPERING DETECTED: %d/%d blocks compromised",
            report["tampered_count"],
            report["total_blocks"],
        )

    return jsonify(report), 200


@bp.route("/results", methods=["GET"])
def get_results():
    """
    Live vote tally — available before and after election close.
    ---
    tags:
      - Admin
    responses:
      200:
        description: Vote tally
    """
    results = (
        db.session.query(Vote.candidate_id, func.count(Vote.id).label("vote_count"))
        .group_by(Vote.candidate_id)
        .order_by(func.count(Vote.id).desc())
        .all()
    )

    tally = []
    for r in results:
        candidate = Candidate.query.get(r.candidate_id)
        tally.append(
            {
                "candidate_id": r.candidate_id,
                "candidate_name": candidate.candidate_name if candidate else "Unknown",
                "party": candidate.party if candidate else "Unknown",
                "vote_count": r.vote_count,
            }
        )

    total_votes = Vote.query.count()
    total_voters = Voter.query.count()
    election = _get_or_init_election()

    return jsonify(
        {
            "election_status": election.status,
            "tally": tally,
            "total_votes": total_votes,
            "total_registered": total_voters,
            "turnout_percent": round(total_votes / total_voters * 100, 1) if total_voters else 0,
        }
    ), 200
