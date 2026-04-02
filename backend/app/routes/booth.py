from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
from sqlalchemy import func
from app.db import db
from app.models import Voter, Vote, Candidate
from app.services.vote_service import encrypt_vote
from app.services.blockchain_service import create_block, get_chain_status

logger = logging.getLogger(__name__)
bp = Blueprint("booth", __name__, url_prefix="/api")


def _get_or_create_nota_candidate():
  """Return NOTA candidate row, creating one if missing."""
  nota = Candidate.query.filter(func.lower(Candidate.candidate_name) == "nota").first()
  if nota:
    return nota

  nota = Candidate(
    candidate_name="NOTA",
    party="None of the Above",
    constituency="All Constituencies",
  )
  db.session.add(nota)
  db.session.flush()
  return nota


@bp.route("/cast_vote", methods=["POST"])
def cast_vote():
    """
    Cast a vote for a candidate at the voting booth.
    ---
    tags:
      - Voting Booth
    summary: Cast a vote
    description: >
      Receive EPIC ID and candidate ID, verify voter hasn't voted,
      encrypt vote, and record to blockchain.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            epic_id:
              type: string
              example: "ABC1234567"
            candidate_id:
              type: integer
              example: 1
    responses:
      201:
        description: Vote cast successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: "vote_cast"
            block_hash:
              type: string
              example: "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
      400:
        description: Invalid input or voter already voted
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Already voted"
      404:
        description: EPIC or candidate not found
        schema:
          type: object
          properties:
            error:
              type: string
              example: "EPIC not found"
      500:
        description: Processing error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error during vote casting"
    """
    data = request.get_json()
    
    # Validate input
    if not data or "epic_id" not in data or "candidate_id" not in data:
      return jsonify({"error": "epic_id and candidate_id required"}), 400
    
    epic_id = data["epic_id"]
    raw_candidate_id = data["candidate_id"]
    
    try:
        # 1. Validate EPIC exists in voter table
        voter = Voter.query.filter_by(epic_id=epic_id).first()
        if not voter:
            logger.warning(f"Vote attempt with invalid EPIC: {epic_id}")
            return jsonify({"error": "EPIC not found"}), 404

        # 2. Check if voter already voted
        if voter.has_voted:
            logger.warning(f"Double vote attempt by voter {voter.id} with EPIC {epic_id}")
            return jsonify({"error": "Already voted"}), 400
        
        # Double-check using Vote table as backup
        existing_vote = Vote.query.filter_by(epic_id=epic_id).first()
        if existing_vote:
            logger.warning(f"Vote already recorded for EPIC {epic_id}")
            if not voter.has_voted:
                voter.has_voted = True
                db.session.commit()
            return jsonify({"error": "Already voted"}), 400
        
        # 3. Validate candidate exists (accept int IDs and "nota" string)
        candidate_id = None
        candidate = None

        try:
          candidate_id = int(raw_candidate_id)
          candidate = Candidate.query.get(candidate_id)
        except (TypeError, ValueError):
          if str(raw_candidate_id).strip().lower() == "nota":
            candidate = _get_or_create_nota_candidate()
          if candidate:
            candidate_id = candidate.id

        if not candidate:
            logger.error(f"Invalid candidate_id: {raw_candidate_id}")
            return jsonify({"error": "Candidate not found"}), 404

        # 4. Encrypt vote
        encrypted_vote = encrypt_vote(candidate_id, epic_id)
        
        # 5. Generate blockchain block hash
        chain_status = get_chain_status()
        if chain_status["last_block_hash"]:
            previous_hash = chain_status["last_block_hash"]
        else:
            previous_hash = "0" * 64
        
        vote_data = {
            "epic_id": epic_id,
            "candidate_id": candidate_id
        }
        timestamp = datetime.utcnow()
        block_hash = create_block(previous_hash, vote_data, timestamp)
        
        # 6. Store vote record
        vote = Vote(
            epic_id=epic_id,
            candidate_id=candidate_id,
            encrypted_vote=encrypted_vote,
            timestamp=timestamp,
            block_hash=block_hash
        )
        db.session.add(vote)
        
        # 7. Mark voter as voted
        voter.has_voted = True
        db.session.commit()
        
        logger.info(f"✓ Vote cast successfully for EPIC {epic_id}, candidate {candidate_id}")
        return jsonify({
            "status": "vote_cast",
            "block_hash": block_hash
        }), 201
    
    except Exception as e:
        logger.error(f"Vote casting error: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@bp.route("/chain_status", methods=["GET"])
def chain_status():
    """
    Get the status of the vote blockchain.
    ---
    tags:
      - Voting Booth
    summary: Check blockchain integrity
    description: >
      Verify the integrity of the vote blockchain and return chain statistics.
    responses:
      200:
        description: Chain status
        schema:
          type: object
          properties:
            length:
              type: integer
              example: 15
            valid:
              type: boolean
              example: true
            last_block_hash:
              type: string
              example: "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
    """
    status = get_chain_status()
    return jsonify(status), 200
