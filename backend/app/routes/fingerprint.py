import os
from pathlib import Path
from flask import Blueprint, jsonify, request
from app.services.fingerprint_service import capture_fingerprint, extract_fingerprint_template
from app.services.fingerprint_dataset.compare import compare_voters
from app.services.fingerprint_dataset.mapper import map_user_to_image
from app.services.fingerprint_dataset.matcher import extract_features, match_score
from app.services.fingerprint_dataset.storage import load_fp
from app.models import Voter

bp = Blueprint("fingerprint", __name__, url_prefix="/api/fingerprint")

_DATASET_BASE = Path(__file__).resolve().parents[2] / "data" / "fingerprints"


@bp.route("/capture", methods=["POST"])
def capture():
    """
    Capture fingerprint from FM220U RD Service.
    ---
    tags:
      - Fingerprint
    summary: Capture fingerprint biometric
    description: >
      Connects to FM220U RD Service and captures a fingerprint.
      Simply captures and returns the fingerprint template.
    responses:
      200:
        description: Fingerprint captured successfully
        schema:
          type: object
          properties:
            message:
              type: string
              example: "Fingerprint captured successfully"
      500:
        description: RD Service error
        schema:
          type: object
          properties:
            error:
              type: string
              example: "RD Service not available"
    """
    # --- Part 3: Deterministic dataset identity check (research layer, silent) ---
    try:
        data = request.get_json(silent=True) or {}
        epic_id = data.get("epic_id")
        if epic_id:
            voter = Voter.query.filter_by(epic_id=epic_id).first()
            if voter:
                expected_image = map_user_to_image(voter.aadhaar_hash)
                if expected_image:
                    expected_path = os.path.join(_DATASET_BASE, expected_image)
                    current_desc = extract_features(expected_path)
                    stored_desc = load_fp(voter.id)
                    if current_desc is not None and stored_desc is not None:
                        score = match_score(stored_desc, current_desc)
                        print("Deterministic fingerprint score:", score)
                        if score < 20:
                            return jsonify({
                                "error": "Fingerprint identity mismatch",
                                "score": score
                            }), 403
    except Exception as _dataset_err:
        # Never block the RD capture flow due to research-layer errors
        pass

    # --- Part 4: Live RD Service capture (unchanged) ---
    try:
        xml_response = capture_fingerprint()

        # Extract fingerprint data
        result = extract_fingerprint_template(xml_response)

        # Just capture - no matching, no comparison
        return jsonify({
            "message": "Fingerprint captured successfully"
        }), 200

    except Exception as e:
        return jsonify({
            "error": str(e)
        }), 500


@bp.route("/dataset-compare", methods=["POST"])
def dataset_compare():
    """Research-only fingerprint similarity comparison for admin diagnostics."""
    try:
        data = request.json or {}
        voter1_id = data.get("voter1_id")
        voter2_id = data.get("voter2_id")

        if voter1_id is None or voter2_id is None:
            return jsonify({"error": "voter1_id and voter2_id are required"}), 400

        score = compare_voters(voter1_id, voter2_id)
        return jsonify({
            "voter1_id": str(voter1_id),
            "voter2_id": str(voter2_id),
            "similarity_score": int(score),
            "unique_identity": bool(score < 30),
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
