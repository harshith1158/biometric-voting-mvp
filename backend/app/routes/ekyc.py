from flask import Blueprint, request, jsonify
from app.services.ekyc_service import validate_aadhaar, hash_aadhaar, generate_ekyc_data, generate_epic_deterministic
from app.db import db
from app.models import Voter
from datetime import datetime

bp = Blueprint("ekyc", __name__, url_prefix="/api")

bp = Blueprint("ekyc", __name__, url_prefix="/api")


@bp.route("/ekyc", methods=["POST"])
def ekyc_verification():
    """
    Simulate Aadhaar eKYC verification.
    ---
    tags:
      - eKYC
    summary: Verify Aadhaar and generate eKYC data
    description: >
      Validate Aadhaar number, generate secure hash, and simulate eKYC data generation.
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
    responses:
      200:
        description: eKYC verification successful
        schema:
          type: object
          properties:
            status:
              type: string
              example: "verified"
            aadhaar_hash:
              type: string
              example: "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
            data:
              type: object
              properties:
                name:
                  type: string
                  example: "Arjun Reddy"
                dob:
                  type: string
                  example: "1990-05-15"
                gender:
                  type: string
                  example: "Male"
                address:
                  type: string
                  example: "Hyderabad"
                phone:
                  type: string
                  example: "9876543210"
      400:
        description: Invalid Aadhaar
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Invalid Aadhaar number"
    """
    data = request.get_json()
    if not data or "aadhaar" not in data:
        return jsonify({"error": "Aadhaar number required"}), 400

    aadhaar = data["aadhaar"]
    if not validate_aadhaar(aadhaar):
        return jsonify({"error": "Invalid Aadhaar number"}), 400

    aadhaar_hash = hash_aadhaar(aadhaar)
    ekyc_data = generate_ekyc_data(aadhaar)

    return jsonify({
        "status": "verified",
        "aadhaar_hash": aadhaar_hash,
        "data": ekyc_data
    }), 200


@bp.route("/register_voter", methods=["POST"])
def register_voter():
    """
    Register a voter with eKYC data.
    ---
    tags:
      - eKYC
    summary: Register voter using eKYC data
    description: >
      Generate EPIC and create voter record with provided eKYC data.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            aadhaar_hash:
              type: string
              example: "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
            name:
              type: string
              example: "Arjun Reddy"
            dob:
              type: string
              example: "1990-05-15"
            gender:
              type: string
              example: "Male"
            address:
              type: string
              example: "Hyderabad"
            phone:
              type: string
              example: "9876543210"
    responses:
      201:
        description: Voter registered successfully
        schema:
          type: object
          properties:
            status:
              type: string
              example: "registered"
            epic_id:
              type: string
              example: "ABC1234567"
      400:
        description: Invalid input
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Missing required fields"
    """
    data = request.get_json()
    required_fields = ["aadhaar_hash", "name", "dob", "gender", "address", "phone"]
    if not data or not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        dob = datetime.strptime(data["dob"], "%Y-%m-%d").date()
    except ValueError:
        return jsonify({"error": "Invalid DOB format"}), 400

    # Create voter with temporary EPIC (will be regenerated)
    voter = Voter(
        aadhaar_hash=data["aadhaar_hash"],
        name=data["name"],
        dob=dob,
        gender=data["gender"],
        address=data["address"],
        phone=data["phone"],
        epic_id="TEMP"  # Temporary, will be replaced after getting voter ID
    )

    db.session.add(voter)
    db.session.flush()  # Flush to get the ID without committing
    
    # Generate deterministic EPIC based on voter ID
    epic_id = generate_epic_deterministic(str(voter.id))
    voter.epic_id = epic_id
    
    db.session.commit()

    return jsonify({
        "status": "registered",
        "epic_id": epic_id
    }), 201