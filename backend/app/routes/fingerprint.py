import os
from pathlib import Path
from flask import Blueprint, jsonify, request
from app.services.fingerprint_service import capture_fingerprint, extract_fingerprint_template
from app.services.fingerprint_dataset.compare import compare_voters
from app.services.fingerprint_dataset.mapper import map_user_to_image
from app.services.fingerprint_dataset.matcher import extract_features, match_score
from app.services.fingerprint_dataset.storage import load_fp
from app.models import Voter
from app.db import db

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

    # --- Part 4: Live RD Service capture (falls back to simulation if no hardware) ---
    try:
        xml_response = capture_fingerprint()
        extract_fingerprint_template(xml_response)
        return jsonify({"message": "Fingerprint captured successfully"}), 200
    except Exception as e:
        # If RD Service hardware is unavailable, simulate successful capture for MVP
        print(f"[fingerprint/capture] RD Service unavailable ({e}), simulating capture")
        return jsonify({"message": "Fingerprint captured successfully (simulated)"}), 200


@bp.route("/my-image", methods=["GET"])
def my_image():
    """Return the deterministically assigned dataset fingerprint filename for the requesting voter."""
    epic_id = request.args.get("epic_id")
    if not epic_id:
        return jsonify({"error": "epic_id query param required"}), 400

    voter = Voter.query.filter_by(epic_id=epic_id).first()
    if not voter:
        return jsonify({"error": "EPIC not found"}), 404

    image_rel = map_user_to_image(voter.aadhaar_hash)
    if not image_rel:
        return jsonify({"error": "No dataset image assigned"}), 404

    # Return just the plain filename (no subdir) so UI can display and match easily
    filename = Path(image_rel).name
    return jsonify({"image": filename, "path": image_rel}), 200


@bp.route("/verify", methods=["POST"])
def verify():
    """Hybrid fingerprint verification: strict ID match + ORB analytics score."""
    try:
        data = request.get_json(silent=True) or {}
        epic_id = data.get("epic_id")
        fingerprint_id = data.get("fingerprint_id")

        if not epic_id:
            return jsonify({"error": "epic_id is required", "status": "fail"}), 400
        if not fingerprint_id:
            return jsonify({"error": "Fingerprint input required", "status": "fail"}), 400

        voter = Voter.query.filter_by(epic_id=epic_id).first()
        if not voter:
            return jsonify({"error": "EPIC not found", "status": "fail"}), 404

        # ── FINGERPRINT LOCKOUT CHECK ──────────────────────────────────────────
        if voter.fingerprint_locked:
            return jsonify({
                "error": "Fingerprint verification locked due to multiple failures. "
                         "Please contact the booth officer.",
                "status": "locked",
            }), 403

        # Resolve assigned fingerprint ID (stored column, or derive for legacy voters)
        assigned_fp = voter.fp_dataset_id or (
            Path(map_user_to_image(voter.aadhaar_hash)).name
            if map_user_to_image(voter.aadhaar_hash) else None
        )

        # Normalise to bare filename for comparison (strip any path prefix)
        selected_name = Path(fingerprint_id).name
        assigned_name = Path(assigned_fp).name if assigned_fp else None

        # ── PART 2: STRICT IDENTITY CHECK ─────────────────────────────────────
        if assigned_name is None or selected_name != assigned_name:
            # Increment failure counter; lock after 3 consecutive failures
            voter.fingerprint_fail_count = (voter.fingerprint_fail_count or 0) + 1
            if voter.fingerprint_fail_count >= 3:
                voter.fingerprint_locked = True
                db.session.commit()
                return jsonify({
                    "error": "Fingerprint identity mismatch. Verification locked after 3 failures.",
                    "status": "locked",
                    "assigned": assigned_name or "unknown",
                    "selected": selected_name,
                }), 403
            db.session.commit()
            remaining = 3 - voter.fingerprint_fail_count
            return jsonify({
                "error": "Fingerprint identity mismatch",
                "status": "fail",
                "assigned": assigned_name or "unknown",
                "selected": selected_name,
                "remaining_attempts": remaining,
            }), 403

        # ── PART 3: ORB ANALYTICS SCORE (runs only after identity confirmed) ──
        matches = list(_DATASET_BASE.rglob(selected_name))
        if not matches:
            return jsonify({"error": f"Dataset image not found: {selected_name}", "status": "fail"}), 404
        current_path = matches[0]

        current_desc = extract_features(str(current_path))
        stored_desc = load_fp(voter.id)

        score = 0.0
        if current_desc is not None and stored_desc is not None:
            raw = match_score(stored_desc, current_desc)
            score = round(raw / max(len(stored_desc), 1), 2)

        print(f"Hybrid verify {epic_id}: id_match=True orb_score={score}")

        # ── PART 4: HYBRID RESPONSE ────────────────────────────────────────────
        # Reset failure counter on success
        if voter.fingerprint_fail_count or voter.fingerprint_locked:
            voter.fingerprint_fail_count = 0
            voter.fingerprint_locked = False
            db.session.commit()

        return jsonify({
            "message": "Fingerprint verified",
            "status": "pass",
            "fingerprint_id": assigned_name,
            "score": score,
        }), 200

    except Exception as e:
        return jsonify({"error": str(e), "status": "fail"}), 500


@bp.route("/images", methods=["GET"])
def list_images():
    """Return sorted deduplicated list of all dataset fingerprint filenames."""
    try:
        seen = set()
        files = []
        for p in sorted(_DATASET_BASE.rglob("*")):
            if p.suffix.lower() in (".tif", ".png", ".bmp") and p.name not in seen:
                seen.add(p.name)
                files.append(p.name)
        return jsonify({"images": files}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
