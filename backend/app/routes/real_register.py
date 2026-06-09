import uuid
import hashlib
import json
import logging
import re
import numpy as np
from flask import Blueprint, request, jsonify
from app.models import Voter
from app.db import db
from app.services.otp_service import create_otp_session, verify_otp
from app.services.election_guard import is_election_open
from datetime import datetime

bp = Blueprint("real_register", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


def hash_aadhaar(aadhaar: str) -> str:
    """Hash Aadhaar using SHA256"""
    return hashlib.sha256(aadhaar.encode()).hexdigest()


def generate_epic_id() -> str:
    """Generate unique EPIC ID"""
    return f"EPIC{uuid.uuid4().hex[:8].upper()}"


def cosine_similarity(embedding1, embedding2) -> float:
    """Compute cosine similarity between two embeddings"""
    try:
        arr1 = np.array(embedding1, dtype=np.float32)
        arr2 = np.array(embedding2, dtype=np.float32)
        
        dot_product = np.dot(arr1, arr2)
        norm1 = np.linalg.norm(arr1)
        norm2 = np.linalg.norm(arr2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    except Exception as e:
        logger.error(f"Cosine similarity error: {str(e)}")
        return 0.0
def validate_full_name(name: str) -> tuple:
    """
    Validate name:
    - Must contain only letters and spaces (no digits, no special chars)
    - Must have at least two words (first name + last name)
    Returns (is_valid: bool, error_message: str)
    """
    if not name or len(name.strip()) < 2:
        return False, "Name is required"
    if not re.match(r'^[A-Za-z\s]+$', name):
        return False, "Name must contain only letters and spaces — no numbers or special characters"
    words = [w for w in name.split() if w]
    if len(words) < 2:
        return False, "Full name is required — please provide both first name and last name"
    return True, ""


@bp.route("/send-otp", methods=["POST"])
def send_otp():
    """
    Send OTP to phone number (mock - prints to console)
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            phone:
              type: string
              example: "9876543210"
    responses:
      200:
        description: OTP sent successfully
        schema:
          type: object
          properties:
            status:
              type: string
            message:
              type: string
      400:
        description: Invalid phone number
    """
    print("[API] /send-otp endpoint hit")
    try:
        data = request.json
        print(f"[API] Request data: {data}")
        if not data or not data.get("phone"):
            return jsonify({"error": "Phone number is required"}), 400
        
        phone = str(data.get("phone")).strip()
        print(f"[API] Phone received: {phone}")
        
        if not phone.isdigit() or len(phone) != 10:
            print(f"[API] Invalid phone: {phone} (isdigit={phone.isdigit()}, len={len(phone)})")
            return jsonify({"error": "Invalid phone number. Must be 10 digits"}), 400
        
        otp, otp_hash = create_otp_session(phone)
        print(f"[API] OTP created: {otp}")
        
        # Mock mode: log OTP clearly through Flask logger so it always appears
        logger.warning(f"\n{'='*50}")
        logger.warning(f"[MOCK OTP] Phone: {phone}")
        logger.warning(f"[MOCK OTP] OTP Code: {otp}")
        logger.warning(f"[MOCK OTP] Valid for 10 minutes")
        logger.warning(f"{'='*50}")
        # Also flush stdout in case buffering hides print output
        import sys
        print(f"\n{'='*50}", flush=True)
        print(f"[MOCK OTP] Phone: {phone}", flush=True)
        print(f"[MOCK OTP] OTP Code: {otp}", flush=True)
        print(f"[MOCK OTP] Valid for 10 minutes", flush=True)
        print(f"{'='*50}\n", flush=True)
        sys.stdout.flush()

        logger.info(f"OTP sent to phone: {phone[:6]}***")
        
        return jsonify({
            "status": "success",
            "message": "OTP sent to your registered mobile",
            "phone_masked": f"{phone[:3]}****{phone[-2:]}"
        }), 200
    
    except Exception as e:
        logger.error(f"Send OTP error: {str(e)}")
        return jsonify({"error": f"Failed to send OTP: {str(e)}"}), 500


@bp.route("/verify-otp", methods=["POST"])
def verify_otp_endpoint():
    """
    Verify OTP for phone number
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            phone:
              type: string
              example: "9876543210"
            otp:
              type: string
              example: "123456"
    responses:
      200:
        description: OTP verified successfully
      400:
        description: Invalid or expired OTP
    """
    print("[API] /verify-otp endpoint hit")
    print(f"[API] Headers: {dict(request.headers)}")
    print(f"[API] Content-Type: {request.content_type}")
    print(f"[API] Raw data: {request.data}")
    
    try:
        data = request.get_json(force=True)  # Force parse even if content-type is wrong
        print(f"[API] Parsed JSON: {data}")
        if not data:
            print("[API] No JSON data after parsing")
            return jsonify({"error": "Request body required"}), 400
        
        phone = str(data.get("phone", "")).strip()
        otp = str(data.get("otp", "")).strip()
        print(f"[API] Extracted: phone='{phone}' (len={len(phone)}), otp='{otp}' (len={len(otp)})")
        
        if not phone or not otp:
            print(f"[API] Validation failed: phone={bool(phone)}, otp={bool(otp)}")
            return jsonify({"error": "Phone and OTP are required"}), 400
        
        success, message = verify_otp(phone, otp)
        print(f"[API] OTP verification result: success={success}, message={message}")
        
        if not success:
            logger.warning(f"OTP verification failed for phone: {phone[:6]}***")
            return jsonify({"error": message}), 400
        
        logger.info(f"OTP verified for phone: {phone[:6]}***")
        
        return jsonify({
            "status": "success",
            "message": message
        }), 200
    
    except Exception as e:
        logger.error(f"Verify OTP error: {str(e)}")
        return jsonify({"error": f"Verification failed: {str(e)}"}), 500


@bp.route("/real-register", methods=["POST"])
def real_register():
    """
    Register real user with face embedding and liveness score
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
            phone:
              type: string
              example: "9876543210"
            name:
              type: string
              example: "John Doe"
            state:
              type: string
              example: "Karnataka"
            face_embedding:
              type: array
              items:
                type: number
              example: [0.1, 0.2, 0.3]
            liveness_score:
              type: number
              example: 0.92
    responses:
      201:
        description: User registered successfully
        schema:
          type: object
          properties:
            epic_id:
              type: string
            status:
              type: string
      400:
        description: Duplicate Aadhaar or validation error
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        aadhaar = str(data.get("aadhaar", "")).strip()
        phone = str(data.get("phone", "")).strip()
        name = str(data.get("name", "")).strip()
        dob_str = str(data.get("dob", "")).strip()
        gender = str(data.get("gender", "")).strip()
        state = str(data.get("state", "")).strip()
        face_embedding = data.get("face_embedding")
        liveness_score = data.get("liveness_score", 0.0)
        profile_image = data.get("profile_image", None)
        
        # Validate inputs
        if not all([aadhaar, phone, name, state, face_embedding]):
            return jsonify({"error": "Missing required fields"}), 400

        # Election guard — block new registrations when election is closed
        if not is_election_open():
            logger.warning("[REAL_REGISTER] Blocked — election is closed")
            return jsonify({"error": "Election is closed. New registrations are not permitted."}), 403

        if not aadhaar.isdigit() or len(aadhaar) != 12:
            return jsonify({"error": "Invalid Aadhaar number"}), 400

        if not phone.isdigit() or len(phone) != 10:
            return jsonify({"error": "Invalid phone number"}), 400

        # Validate name — letters only, first + last name required
        name_valid, name_error = validate_full_name(name)
        if not name_valid:
            return jsonify({"error": name_error}), 400

        if liveness_score < 0.70:
            return jsonify({"error": "Liveness score below threshold (0.70)"}), 400

        # Check for duplicate Aadhaar
        aadhaar_hash = hash_aadhaar(aadhaar)
        exact_existing = Voter.query.filter_by(aadhaar_hash=aadhaar_hash, phone=phone, name=name).first()
        if exact_existing:
          logger.warning("Exact duplicate re-registration blocked for EPIC=%s", exact_existing.epic_id)
          return jsonify({
            "error": "This voter is already registered with the same name, Aadhaar and mobile number.",
            "epic_id": exact_existing.epic_id,
          }), 400

        existing_voter = Voter.query.filter_by(aadhaar_hash=aadhaar_hash).first()

        if existing_voter:
            if existing_voter.has_voted:
                logger.warning(f"Re-registration blocked — voter {existing_voter.epic_id} already voted")
                return jsonify({
                    "error": "You have already voted. Re-registration is not allowed.",
                    "epic_id": existing_voter.epic_id
                }), 403
            logger.warning(f"Duplicate Aadhaar registration attempt for hash: {aadhaar_hash[:8]}...")
            return jsonify({
                "error": "This Aadhaar is already registered",
                "epic_id": existing_voter.epic_id
            }), 400

        # Check for duplicate phone number
        existing_phone = Voter.query.filter_by(phone=phone).first()
        if existing_phone:
            logger.warning(f"Duplicate phone registration attempt: {phone[:6]}***")
            return jsonify({"error": "This mobile number is already registered with another voter"}), 400

        # Generate EPIC ID
        epic_id = generate_epic_id()

        # Convert face_embedding to JSON string for storage
        face_embedding_json = json.dumps(face_embedding)

        # Validate and parse DOB; enforce age >= 18
        if not dob_str:
            return jsonify({"error": "Date of birth is required"}), 400
        try:
            dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid DOB format. Use YYYY-MM-DD"}), 400

        today = datetime.utcnow().date()
        if dob >= today:
            return jsonify({"error": "Date of birth cannot be in the future"}), 400
        age = (today - dob).days // 365
        if age < 18:
            return jsonify({"error": "Voter must be at least 18 years old"}), 400

        # Create new voter with real_user flag
        profile_data = json.dumps({
            "name": name,
            "gender": gender if gender else "Not Specified",
            "dob": dob_str,
            "state": state,
            "phone": phone,
        })
        new_voter = Voter(
            aadhaar_hash=aadhaar_hash,
            name=name,
            phone=phone,
            epic_id=epic_id,
            face_embedding=face_embedding_json,
            liveness_score=liveness_score,
            is_real_user=True,
            dob=dob,
            gender=gender if gender else "Not Specified",
            address=state,
            profile_image=profile_image,
            profile_data=profile_data,
        )

        db.session.add(new_voter)
        db.session.commit()

        logger.info(f"Real user registered: EPIC={epic_id}, phone={phone[:6]}***, liveness={liveness_score}")
        
        return jsonify({
            "status": "success",
            "epic_id": epic_id,
            "voter_id": str(new_voter.id),
            "message": "Registration successful.",
            "name": name
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Real registration error: {str(e)}")
        return jsonify({"error": f"Registration failed: {str(e)}"}), 500


@bp.route("/face-verify", methods=["POST"])
def face_verify():
    """
    Verify user identity by matching live face embedding with stored embedding
    ---
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            epic_id:
              type: string
              example: "EPIC12345678"
            live_embedding:
              type: array
              items:
                type: number
              example: [0.1, 0.2, 0.3]
    responses:
      200:
        description: Face verification successful
        schema:
          type: object
          properties:
            status:
              type: string
            similarity:
              type: number
            match:
              type: boolean
      400:
        description: Invalid input or verification failed
    """
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Request body required"}), 400
        
        epic_id = str(data.get("epic_id", "")).strip()
        live_embedding = data.get("live_embedding")
        
        if not epic_id or not live_embedding:
            return jsonify({"error": "EPIC ID and live embedding required"}), 400
        
        # Fetch voter from database
        voter = Voter.query.filter_by(epic_id=epic_id).first()
        
        if not voter:
            logger.warning(f"Face verification failed: EPIC {epic_id} not found")
            return jsonify({"error": "Voter not found"}), 404
        
        if not voter.face_embedding:
            logger.warning(f"Face verification failed: No stored embedding for EPIC {epic_id}")
            return jsonify({"error": "No stored face embedding for this voter"}), 400
        
        # Parse stored embedding
        try:
            stored_embedding = json.loads(voter.face_embedding)
        except json.JSONDecodeError:
            logger.error(f"Face embedding decode error for EPIC {epic_id}")
            return jsonify({"error": "Stored embedding data corrupted"}), 500
        
        # Compute cosine similarity
        similarity = cosine_similarity(stored_embedding, live_embedding)
        
        # Threshold for face match (lower for landmark-based embeddings)
        SIMILARITY_THRESHOLD = 0.60
        match = similarity >= SIMILARITY_THRESHOLD
        
        logger.info(f"Face verification: EPIC={epic_id}, similarity={similarity:.4f}, match={match}")
        
        if match:
            return jsonify({
                "status": "success",
                "message": "Face verified successfully",
                "similarity": float(similarity),
                "match": True,
                "name": voter.name
            }), 200
        else:
            return jsonify({
                "status": "failure",
                "message": "Face does not match stored record",
                "similarity": float(similarity),
                "match": False
            }), 400
    
    except Exception as e:
        logger.error(f"Face verification error: {str(e)}")
        return jsonify({"error": f"Face verification failed: {str(e)}"}), 500
