import re
from flask import Blueprint, request, jsonify
from app.services import otp_service

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


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

    if not aadhaar or not validate_aadhaar(aadhaar):
        return jsonify({"error": "Invalid aadhaar format. Must be 12 digits."}), 400

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
    phone = data.get("phone", "").strip()
    otp = data.get("otp", "").strip()

    if not phone or not validate_phone(phone):
        return jsonify({"error": "Invalid phone format."}), 400

    if not otp or not re.match(r"^\d{6}$", otp):
        return jsonify({"error": "Invalid OTP format."}), 400

    verified = otp_service.verify_otp(phone, otp)

    return jsonify({"verified": verified}), 200
