from flask import Blueprint, jsonify
from app.services.fingerprint_service import capture_fingerprint, extract_fingerprint_template

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
      Returns the fingerprint hash for voter authentication.
    responses:
      200:
        description: Fingerprint captured and hashed
        schema:
          type: object
          properties:
            status:
              type: string
              example: "success"
            fingerprint_hash:
              type: string
              example: "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3"
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
        
        # Extract and hash fingerprint data
        result = extract_fingerprint_template(xml_response)
        
        return jsonify({
            "status": "success",
            "fingerprint_hash": result["fingerprint_hash"],
            "quality_score": result["quality_score"]
        }), 200
    
    except Exception as e:
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500
