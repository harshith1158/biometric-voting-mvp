from flask import Blueprint, request, jsonify
from datetime import datetime
from app.db import db
from app.models import Voter, Vote, Candidate
from app.services.fingerprint_service import capture_fingerprint, extract_fingerprint_template
from app.services.vote_service import encrypt_vote
from app.services.blockchain_service import create_block, get_chain_status

bp = Blueprint("booth", __name__, url_prefix="/api")


@bp.route("/cast_vote", methods=["POST"])
def cast_vote():
    """
    Cast a vote for a candidate using fingerprint authentication.
    ---
    tags:
      - Voting Booth
    summary: Cast a vote with fingerprint verification
    description: >
      Authenticate voter via EPIC ID, capture fingerprint, verify candidate,
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
              example: "Voter has already cast a vote"
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
              example: "RD Service not available"
    """
    data = request.get_json()
    
    # Validate input
    if not data or "epic_id" not in data or "candidate_id" not in data:
        return jsonify({"error": "epic_id and candidate_id required"}), 400
    
    epic_id = data["epic_id"]
    candidate_id = data["candidate_id"]
    
    try:
        # 1. Validate EPIC exists in voter table
        voter = Voter.query.filter_by(epic_id=epic_id).first()
        if not voter:
            return jsonify({"error": "EPIC not found"}), 404
        
        # 2. Check voter has not already voted
        existing_vote = Vote.query.filter_by(epic_id=epic_id).first()
        if existing_vote:
            return jsonify({"error": "Voter has already cast a vote"}), 400
        
        # 3. Validate candidate exists
        candidate = Candidate.query.get(candidate_id)
        if not candidate:
            return jsonify({"error": "Candidate not found"}), 404
        
        # 4. Capture fingerprint
        xml_response = capture_fingerprint()
        fp_result = extract_fingerprint_template(xml_response)
        fingerprint_hash = fp_result["fingerprint_hash"]
        
        # 5. Encrypt vote
        encrypted_vote = encrypt_vote(candidate_id, epic_id)
        
        # 6. Generate blockchain block hash
        # Get the last block hash for previous_hash
        chain_status = get_chain_status()
        if chain_status["last_block_hash"]:
            previous_hash = chain_status["last_block_hash"]
        else:
            # Genesis block
            previous_hash = "0" * 64
        
        vote_data = {
            "epic_id": epic_id,
            "candidate_id": candidate_id,
            "fingerprint_hash": fingerprint_hash
        }
        timestamp = datetime.utcnow()
        block_hash = create_block(previous_hash, vote_data, timestamp)
        
        # 7. Store vote record
        vote = Vote(
            epic_id=epic_id,
            candidate_id=candidate_id,
            encrypted_vote=encrypted_vote,
            fingerprint_hash=fingerprint_hash,
            timestamp=timestamp,
            block_hash=block_hash
        )
        db.session.add(vote)
        db.session.commit()
        
        return jsonify({
            "status": "vote_cast",
            "block_hash": block_hash
        }), 201
    
    except Exception as e:
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
