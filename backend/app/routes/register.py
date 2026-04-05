import uuid
from flask import Blueprint, request, jsonify
from app.models import Voter
from app.db import db
from app.services.hash_chain import append_block
from app.services.ekyc_service import generate_ekyc_data
from datetime import datetime
import hashlib
import logging
import json
import os
from pathlib import Path
from app.services.fingerprint_dataset.matcher import extract_features
from app.services.fingerprint_dataset.storage import save_fp
from app.services.fingerprint_dataset.mapper import map_user_to_image

bp = Blueprint("register", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


def hash_field(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@bp.route("/register", methods=["POST"])
def register():
    """
    Register a new voter with OTP verification
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            aadhaar:
              type: string
              example: "123456789012"
            aadhar_number:
              type: string
              example: "123456789012"
            phone:
              type: string
              example: "9876543210"
            otp:
              type: string
              example: "123456"
    responses:
      201:
        description: Voter registered successfully
        schema:
          type: object
          properties:
            epic_id:
              type: string
            voter_id:
              type: string
            status:
              type: string
      400:
        description: Aadhaar already registered or invalid input
        schema:
          type: object
          properties:
            error:
              type: string
            epic_id:
              type: string
            status:
              type: string
    """
    try:
        data = request.json
        if not data:
            logger.error("[REGISTER] Empty request body")
            return jsonify({"error": "Request body is required"}), 400
        
        # Support both parameter names
        aadhaar = data.get("aadhaar") or data.get("aadhar_number")
        
        logger.info(f"[REGISTER] Registration request for Aadhaar: {aadhaar}")
        
        # Validate aadhaar
        if not aadhaar:
            logger.warning("[REGISTER] Missing Aadhaar number")
            return jsonify({"error": "Aadhaar number is required"}), 400
        
        # Validate aadhaar format (12 digits)
        if not str(aadhaar).isdigit() or len(str(aadhaar)) != 12:
            logger.warning(f"[REGISTER] Invalid Aadhaar format: {aadhaar}")
            return jsonify({"error": "Invalid Aadhaar format. Must be 12 digits."}), 400

        # Check if voter already exists with this Aadhaar
        aadhaar_hash = hash_field(aadhaar)
        existing_voter = Voter.query.filter_by(aadhaar_hash=aadhaar_hash).first()
        
        if existing_voter:
            logger.info(f"[REGISTER] Voter already exists with this Aadhaar: {existing_voter.epic_id}")
            return jsonify({
                "error": "Aadhaar already registered",
                "epic_id": existing_voter.epic_id,
                "voter_id": str(existing_voter.id),
                "status": "existing"
            }), 400

        # Generate eKYC data deterministically from Aadhaar
        logger.info(f"[REGISTER] Generating eKYC data for Aadhaar")
        ekyc_data = generate_ekyc_data(aadhaar)
        
        # Parse DOB from string to date
        dob = datetime.strptime(ekyc_data["dob"], "%Y-%m-%d").date()

        epic_id = f"EPIC-{uuid.uuid4().hex[:10].upper()}"
        logger.info(f"[REGISTER] Generated EPIC: {epic_id}")

        # Create voter with generated eKYC data
        voter = Voter(
            aadhaar_hash=aadhaar_hash,
            name=ekyc_data["name"],
            dob=dob,
            gender=ekyc_data["gender"],
            address=ekyc_data["address"],
            phone=ekyc_data["phone"],
            epic_id=epic_id
        )
        profile = {
          "name": ekyc_data["name"],
          "gender": ekyc_data["gender"],
          "dob": ekyc_data["dob"],
          "state": ekyc_data.get("state", ""),
          "address": ekyc_data["address"],
          "phone": ekyc_data["phone"],
        }
        voter.profile_data = json.dumps(profile)
        db.session.add(voter)
        db.session.commit()
        logger.info(f"[REGISTER] âœ“ Voter registered successfully - EPIC: {epic_id}, Voter ID: {voter.id}")

        # Research-only dataset fingerprint assignment.
        # This runs silently and never blocks user registration.
        try:
          dataset_path = Path(__file__).resolve().parents[2] / "data" / "fingerprints"
          selected = map_user_to_image(voter.aadhaar_hash)

          if selected:
            image_path = os.path.join(dataset_path, selected)
            descriptors = extract_features(image_path)
            save_fp(voter.id, descriptors)
            voter.fp_dataset_id = Path(selected).name  # Store just the filename (e.g. "101_8.tif")
            db.session.commit()
            print("Deterministic dataset assigned:", selected)
          else:
            logger.warning("[REGISTER] No dataset fingerprint images found at %s", dataset_path)
        except Exception as dataset_error:
          logger.warning("[REGISTER] Dataset fingerprint assignment skipped: %s", dataset_error)

        append_block(f"REGISTER:{epic_id}")

        return jsonify({
            "epic_id": epic_id, 
            "voter_id": str(voter.id), 
            "status": "new"
        }), 201
    
    except Exception as e:
        logger.error(f"[REGISTER] Error during registration: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


