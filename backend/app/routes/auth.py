import re
import hashlib
from flask import Blueprint, request, jsonify
from app.services import otp_service
from app.services.ekyc_service import generate_ekyc_data
from app.services.attempt_tracker import is_locked, get_lockout_remaining, record_failure, reset_attempts

bp = Blueprint("auth", __name__, url_prefix="/api/auth")

# In-memory demo OTP store keyed by Aadhaar hash.
otp_store = {}


def hash_field(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def validate_aadhaar(aadhaar: str) -> bool:
    return bool(re.match(r"^\d{12}$", aadhaar))


def validate_phone(phone: str) -> bool:
    return bool(re.match(r"^\d{10}$", phone))


@bp.route("/request-otp", methods=["POST"])
def request_otp():
    """
    Request OTP for voter registration
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
    responses:
      201:
        description: OTP requested successfully (demo mode returns OTP)
        schema:
          type: object
          properties:
            message:
              type: string
            otp:
              type: string
      400:
        description: Invalid aadhaar or phone format
    """
    data = request.json or {}
    aadhaar = data.get("aadhaar", "").strip()
    phone = data.get("phone", "").strip()

    if aadhaar:
        if not validate_aadhaar(aadhaar):
            return jsonify({"error": "Invalid aadhaar format. Must be 12 digits."}), 400

        ekyc_data = generate_ekyc_data(aadhaar)
        resolved_phone = ekyc_data.get("phone", "")
        if not resolved_phone or not validate_phone(resolved_phone):
            return jsonify({"error": "Unable to resolve registered phone for Aadhaar."}), 400

        seed = int(aadhaar[-6:])
        otp = str(100000 + (seed % 900000))
        aadhaar_hash = hash_field(aadhaar)
        otp_store[aadhaar_hash] = otp
        masked = "XXXXXX" + resolved_phone[-4:]

        return jsonify({
            "message": "OTP sent",
            "phone": masked,
            "otp": otp,  # Demo mode only
        }), 201

    # Backward-compatible fallback for existing phone-based OTP flow.
    if not phone or not validate_phone(phone):
        return jsonify({"error": "Invalid phone format. Must be 10 digits."}), 400

    otp, _ = otp_service.create_otp_session(phone)

    return jsonify({
        "message": "OTP sent successfully",
        "otp": otp  # Demo mode only
    }), 201


@bp.route("/verify-otp", methods=["POST"])
def verify_otp():
    """
    Verify OTP for voter registration
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
        description: OTP verification result
        schema:
          type: object
          properties:
            verified:
              type: boolean
      400:
        description: Invalid phone or OTP format
    """
    data = request.json or {}
    aadhaar = data.get("aadhaar", "").strip()
    phone = data.get("phone", "").strip()
    otp = data.get("otp", "").strip()

    if not otp or not re.match(r"^\d{6}$", otp):
        return jsonify({"error": "Invalid OTP format."}), 400

    if aadhaar:
        if not validate_aadhaar(aadhaar):
            return jsonify({"error": "Invalid aadhaar format. Must be 12 digits."}), 400

        session_key = hashlib.sha256(aadhaar.encode()).hexdigest()

        # Lockout check
        if is_locked(session_key, "otp"):
            remaining = get_lockout_remaining(session_key, "otp")
            return jsonify({"error": f"Too many failed OTP attempts. Please wait {remaining} seconds."}), 429

        # Deterministic OTP: same formula as request-otp, so no in-memory store needed
        seed = int(aadhaar[-6:])
        expected_otp = str(100000 + (seed % 900000))

        if otp != expected_otp:
            result = record_failure(session_key, "otp")
            msg = "Invalid OTP"
            if result["locked"]:
                msg = f"Too many failed attempts. Locked for 15 minutes."
            elif result["remaining_attempts"] > 0:
                msg = f"Invalid OTP. {result['remaining_attempts']} attempt(s) remaining."
            return jsonify({"error": msg, "verified": False}), 400

        reset_attempts(session_key, "otp")
        return jsonify({"verified": True}), 200

    if not phone or not validate_phone(phone):
        return jsonify({"error": "Invalid phone format."}), 400

    session_key = hashlib.sha256(phone.encode()).hexdigest()

    # Lockout check
    if is_locked(session_key, "otp"):
        remaining = get_lockout_remaining(session_key, "otp")
        return jsonify({"error": f"Too many failed OTP attempts. Please wait {remaining} seconds."}), 429

    verified, _ = otp_service.verify_otp(phone, otp)
    if not verified:
        result = record_failure(session_key, "otp")
        msg = "Invalid or expired OTP"
        if result["locked"]:
            msg = "Too many failed attempts. Locked for 15 minutes."
        elif result["remaining_attempts"] > 0:
            msg = f"Invalid OTP. {result['remaining_attempts']} attempt(s) remaining."
        return jsonify({"verified": False, "error": msg}), 400

    reset_attempts(session_key, "otp")
    return jsonify({"verified": verified}), 200
