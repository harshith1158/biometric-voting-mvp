import hashlib
from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import json
import os
from sqlalchemy import func
from app.db import db
from app.models import Voter, Vote, Candidate
from app.services.vote_service import encrypt_vote
from app.services.blockchain_service import create_block, get_chain_status
from app.services.biometric_service import load_image_from_bytes, save_live_face, verify_identity_strict
from app.services.election_guard import is_election_open

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


@bp.route("/verify_face_before_vote", methods=["POST"])
def verify_face_before_vote():
    """
    Verify voter's face BEFORE casting vote at booth using DeepFace.
    
    SECURITY: Must be called before /cast_vote to ensure identity.
    Uses DeepFace.verify() for face comparison (different person → FAIL, same person → PASS).
    """
    logger.info("[BOOTH] /api/verify_face_before_vote POST request")
    
    try:
        # Get EPIC ID from request
        epic_id = request.form.get("epic_id")
        if not epic_id:
            logger.warning("[BOOTH] Missing epic_id")
            return jsonify({"error": "epic_id required"}), 400
        
        # Get image frame from request
        if "frame" not in request.files:
            logger.warning("[BOOTH] No frame in request")
            return jsonify({"error": "No frame uploaded"}), 400
        
        frame_file = request.files["frame"]
        frame_bytes = frame_file.read()
        
        if len(frame_bytes) == 0:
            logger.error("[BOOTH] Empty frame uploaded")
            return jsonify({"error": "Empty frame"}), 400
        
        logger.info(f"[BOOTH] Verifying face for EPIC: {epic_id}")
        
        # Find voter by EPIC
        voter = Voter.query.filter_by(epic_id=epic_id).first()
        if not voter:
            logger.warning(f"[BOOTH] Voter not found for EPIC: {epic_id}")
            return jsonify({"error": "EPIC not found"}), 404
        
        # Check if voter already voted
        if voter.has_voted:
            logger.warning(f"[BOOTH] Access denied - voter {epic_id} already voted")
            return jsonify({"error": "You have already voted. Access denied."}), 403
        
        # Get stored face image path from voter record
        # (stored in face_embedding field as image path)
        if not voter.face_embedding:
            logger.error(f"[BOOTH] No stored face image for EPIC: {epic_id}")
            return jsonify({"error": "Face not registered for this EPIC"}), 400
        
        stored_face_path = voter.face_embedding
        
        if not os.path.exists(stored_face_path):
            logger.error(f"[BOOTH] Stored face image not found: {stored_face_path}")
            return jsonify({"error": "Stored face image file missing"}), 500
        
        logger.info(f"[BOOTH] Loaded stored face image: {stored_face_path}")
        print(f"[BOOTH] Registered face path: {stored_face_path}")
        
        # STRICT: Save live face with MANDATORY face detection
        try:
            frame_image = load_image_from_bytes(frame_bytes)
            live_face_path = save_live_face(frame_image)
            
            if not live_face_path:
                logger.error("[BOOTH] BLOCK: Could not save live face - STRICT face detection failed")
                print(f"[BOOTH] BLOCKED: Live face not detected or multiple faces detected")
                return jsonify({"error": "Face not detected in live capture - only 1 face allowed"}), 400
            
            logger.info(f"[BOOTH] Saved live face image: {live_face_path}")
            print(f"[BOOTH] Saved live image: {live_face_path}")
        except Exception as e:
            logger.error(f"[BOOTH] Error saving live face: {str(e)}", exc_info=True)
            print(f"[BOOTH] EXCEPTION saving live face: {str(e)}")
            return jsonify({"error": "Could not process live frame"}), 400
        
        # STRICT: Identity verification using DeepFace with enforce_detection=True
        try:
            print(f"\n[BOOTH] {'='*80}")
            print(f"[BOOTH] STRICT IDENTITY VERIFICATION")
            result = verify_identity_strict(stored_face_path, live_face_path)
            verified = result.get('verified', False)
            distance = result.get('distance', 1.0)
            error = result.get('error')
            
            logger.info(f"[BOOTH] Verification result: verified={verified}, distance={distance:.4f}")
            
            # STRICT: BLOCK if verification fails - NO EXCEPTIONS, NO FALLBACK
            if not verified:
                logger.error(f"[BOOTH] ✗ IDENTITY VERIFICATION BLOCKED")
                if error:
                    logger.error(f"[BOOTH] Error: {error}")
                print(f"[BOOTH] ✗ IDENTITY MISMATCH - VOTE BLOCKED")
                print(f"[BOOTH] {'='*80}\n")
                return jsonify({
                    "status": "fail",
                    "error": "Identity verification failed. Different person detected.",
                    "verified": False,
                    "distance": round(distance, 4)
                }), 400
            
            # Verification PASSED - Same person confirmed
            logger.info(f"[BOOTH] ✓ Identity verified for EPIC {epic_id}")
            print(f"[BOOTH] ✓ IDENTITY CONFIRMED - Same person, vote allowed")
            print(f"[BOOTH] {'='*80}\n")
            return jsonify({
                "status": "pass",
                "message": "Identity verified - you may cast your vote",
                "verified": True,
                "distance": round(distance, 4)
            }), 200
        
        except Exception as e:
            logger.error(f"[BOOTH] Verification exception: {type(e).__name__}: {str(e)}", exc_info=True)
            print(f"[BOOTH] ✗ VERIFICATION EXCEPTION - VOTE BLOCKED: {str(e)}")
            print(f"[BOOTH] {'='*80}\n")
            return jsonify({"error": f"Identity verification failed: {str(e)}"}), 500
        
        finally:
            # Clean up temporary live face image
            if live_face_path and os.path.exists(live_face_path):
                try:
                    logger.debug(f"[BOOTH] Cleaning up live image: {live_face_path}")
                    os.remove(live_face_path)
                except Exception as cleanup_error:
                    logger.warning(f"[BOOTH] Could not delete live image: {str(cleanup_error)}")
    
    except Exception as e:
        logger.error(f"[BOOTH] Unexpected error: {str(e)}", exc_info=True)
        return jsonify({"error": f"Verification error: {str(e)}"}), 500



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

    # FIX 3: Block vote without fingerprint verification
    if data.get("fingerprint_verified") is not True:
        logger.warning(f"[CAST_VOTE] Vote attempt without fingerprint verification for EPIC: {epic_id}")
        return jsonify({"error": "Fingerprint verification required"}), 403

    # Election guard — block voting after election is declared closed
    if not is_election_open():
        logger.warning(f"[CAST_VOTE] Vote blocked — election is closed (EPIC: {epic_id})")
        return jsonify({"error": "Election is closed. No votes can be cast."}), 403

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
        
        # SECURITY FIX 4: Double-check using Vote table as backup
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
        
        # SECURITY FIX 4: Mark voter as voted to enforce one vote per user
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


@bp.route("/voter_lookup", methods=["GET"])
def voter_lookup():
    """Check if an EPIC ID exists and return basic voter info."""
    epic_id = request.args.get("epic_id", "").strip()
    if not epic_id:
        return jsonify({"error": "epic_id is required"}), 400

    voter = Voter.query.filter_by(epic_id=epic_id).first()
    if not voter:
        return jsonify({"error": "Invalid EPIC ID. No voter found with this ID."}), 404

    if voter.has_voted:
        return jsonify({"error": "This voter has already cast their vote."}), 400

    return jsonify({
        "valid": True,
        "name": voter.name,
        "epic_id": voter.epic_id,
        "is_real_user": voter.is_real_user or False,
        "profile": {
            "name": voter.name or "",
            "gender": voter.gender or "",
            "state": voter.address or "",
            "profile_image": voter.profile_image or "",
        },
    }), 200


@bp.route("/check_aadhaar", methods=["POST"])
def check_aadhaar():
    """Check if an Aadhaar number is already registered."""
    data = request.get_json()
    aadhaar = str(data.get("aadhaar", "")).strip() if data else ""
    if not aadhaar:
        return jsonify({"error": "aadhaar is required"}), 400

    aadhaar_hash = hashlib.sha256(aadhaar.encode()).hexdigest()
    existing = Voter.query.filter_by(aadhaar_hash=aadhaar_hash).first()
    if existing:
        result = {
            "registered": True,
            "has_voted": existing.has_voted or False,
            "epic_id": existing.epic_id,
            "voter_id": str(existing.id),
            "is_real_user": existing.is_real_user or False,
            "profile": {
                "name": existing.name or "",
                "dob": str(existing.dob) if existing.dob else "",
                "gender": existing.gender or "",
                "state": existing.address or "",
                "phone": existing.phone or "",
                "profile_image": existing.profile_image or "",
            },
        }
        return jsonify(result), 200

    return jsonify({"registered": False}), 200
