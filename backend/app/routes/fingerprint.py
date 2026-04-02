from flask import Blueprint, jsonify, request
from app.services.fingerprint_service import capture_fingerprint, extract_fingerprint_template
from app.services.fingerprint_dataset.compare import compare_voters

bp = Blueprint("fingerprint", __name__, url_prefix="/api/fingerprint")


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
    try:
        # Capture fingerprint from RD Service
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
