import uuid
from flask import Blueprint, request, jsonify
from app.models import Voter
from app.db import db
from app.services.hash_chain import append_block
import hashlib

bp = Blueprint("register", __name__, url_prefix="/api")


def hash_field(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@bp.route("/register", methods=["POST"])
def register():
    """
    Register a new voter
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
        description: Voter registered successfully
        schema:
          type: object
          properties:
            epic_id:
              type: string
    """
    data = request.json
    aadhaar = data.get("aadhaar")
    phone = data.get("phone")

    epic_id = f"EPIC-{uuid.uuid4().hex[:10].upper()}"

    voter = Voter(
        aadhaar_hash=hash_field(aadhaar),
        phone_hash=hash_field(phone),
        epic_id=epic_id,
    )
    db.session.add(voter)
    db.session.commit()

    append_block(f"REGISTER:{epic_id}")

    return jsonify({"epic_id": epic_id}), 201