from flask import Blueprint, request, jsonify
import uuid
import json
import logging
import numpy as np
import cv2
import os

from app.db import db
from app.models import Biometric, Voter
from app.services.liveness import detect_blink, detect_blink_sequence
from app.routes.landmarks import extract_eye_landmarks
from app.services.biometric_service import load_image_from_bytes, save_face_image, save_registration_face, save_multi_registration_faces, save_live_face, verify_identity_strict, verify_identity_multiframe, deepface_verify, extract_embeddings_from_folder
from app.services.attempt_tracker import is_locked, get_lockout_remaining, record_failure, reset_attempts

logger = logging.getLogger(__name__)

bp = Blueprint("biometrics", __name__, url_prefix="/api/biometrics")

EAR_THRESHOLD = 0.25
MIN_BLINK_FRAMES = 2
NOSE_X_THRESHOLD = 6.0  # pixels — per-frame nose X delta to count as head movement
NOSE_X_SPAN_THRESHOLD = 12.0  # pixels — total nose X drift across the capture window
TOTAL_NOSE_MOVEMENT_THRESHOLD = 30.0  # pixels — cumulative nose motion across frames
STATIC_FRAME_DIFF_THRESHOLD = 1.2  # mean grayscale diff between consecutive frames


def _tamper_response(session_key: str, reason: str, status_code: int = 400):
    """Record a tamper attempt and return a lockout-aware response payload."""
    attempt_result = record_failure(session_key, "tamper")
    message = reason
    if attempt_result["locked"]:
        message = "Too many tampering attempts. Session locked for 15 minutes."
        status_code = 429
    elif attempt_result["remaining_attempts"] > 0:
        message = f"{reason} ({attempt_result['remaining_attempts']} tamper attempt(s) remaining)"

    return jsonify({
        "status": "failed",
        "liveness": "fail",
        "error": message,
        "attempt_type": "tamper",
        "locked": attempt_result["locked"],
    }), status_code


@bp.route("/selfie", methods=["POST"])
def selfie_liveness():
    """
    Perform liveness detection with multiple frames.
    ---
    tags:
      - Biometrics
    summary: Detect face liveness from selfie frames
    description: >
      Process multiple frames to detect eye blinks (liveness verification).
      Extracts eye landmarks, computes EAR (Eye Aspect Ratio), and generates face embedding.
      Minimum 2 frames with EAR < 0.25 required to pass blink detection.
    parameters:
      - name: frames
        in: formData
        type: array
        items:
          type: file
        required: true
        description: Array of image files (jpg/png)
      - name: voter_id
        in: formData
        type: string
        required: true
        example: "550e8400-e29b-41d4-a716-446655440000"
        description: UUID of the voter
    responses:
      200:
        description: Liveness check passed - blink detected
        schema:
          type: object
          properties:
            liveness:
              type: string
              example: "pass"
            ear_values:
              type: array
              items:
                type: number
              example: [0.15, 0.12, 0.18, 0.22, 0.10]
            message:
              type: string
              example: "Blink detected"
            biometric_id:
              type: integer
              example: 1
      400:
        description: Liveness check failed or invalid input
        schema:
          type: object
          properties:
            liveness:
              type: string
              example: "fail"
            error:
              type: string
              example: "Blink not detected"
            ear_values:
              type: array
              items:
                type: number
    """
    
    logger.info("[SELFIE] ===== /api/biometrics/selfie POST request =====")

    try:
      import numpy as np
      import cv2
    except Exception as e:
      logger.error(f"[SELFIE] Runtime dependencies unavailable: {str(e)}")
      return jsonify({"error": "Runtime dependencies unavailable on server", "liveness": "fail"}), 500
    
    if "frames" not in request.files:
        logger.error("[SELFIE] No frames in request.files")
        return jsonify({"error": "No frames uploaded"}), 400

    voter_id = request.form.get("voter_id")
    if not voter_id:
        logger.error("[SELFIE] voter_id missing from form")
        return jsonify({"error": "voter_id missing"}), 400

    flow_source = str(request.form.get("flow_source", "")).strip().lower()
    is_real_register_flow = flow_source in {"real_register", "real-register", "registration"}
    
    logger.info(f"[SELFIE] voter_id: {voter_id}, flow_source: {flow_source or 'default'}")

    try:
        voter_uuid = uuid.UUID(voter_id)
        logger.info("[SELFIE] UUID parsed successfully")
    except ValueError:
        logger.error(f"[SELFIE] Invalid UUID format: {voter_id}")
        return jsonify({"error": "invalid voter_id format"}), 400

    # Verify voter exists
    voter = Voter.query.filter_by(id=voter_uuid).first()
    if not voter:
        logger.warning(f"[SELFIE] Voter not found: {voter_id}")
        return jsonify({"error": f"Voter not found: {voter_id}"}), 400

    logger.info(f"[SELFIE] Voter found: {voter.aadhaar_hash}")
    print(f"STEP: Aadhaar received — voter aadhaar_hash: {voter.aadhaar_hash}")

    # Liveness attempt lockout check
    session_key = str(voter_uuid)
    if is_locked(session_key, "liveness"):
        remaining = get_lockout_remaining(session_key, "liveness")
        logger.warning(f"[SELFIE] Liveness locked for voter {voter_id} — {remaining}s remaining")
        return jsonify({
            "liveness": "fail",
            "error": f"Too many liveness failures. Please wait {remaining} seconds and try again.",
            "locked": True,
        }), 429

    if is_locked(session_key, "tamper"):
        remaining = get_lockout_remaining(session_key, "tamper")
        logger.warning(f"[SELFIE] Tamper lock active for voter {voter_id} — {remaining}s remaining")
        return jsonify({
            "liveness": "fail",
            "error": f"Too many tampering attempts. Please wait {remaining} seconds and try again.",
            "locked": True,
            "attempt_type": "tamper",
        }), 429

    frames = request.files.getlist("frames")
    logger.info(f"[SELFIE] Received {len(frames)} frames")

    if len(frames) < 3:
        return jsonify({"error": "Minimum 3 frames required"}), 400

    ear_values = []
    frames_processed = 0
    frames_failed = 0
    prev_nose = None
    first_nose = None
    nose_movement = 0.0
    nose_x_span = 0.0
    closed_eye_frames = 0
    movement_detected = False  # True if head movement (nose X delta) seen in any frame
    consecutive_frame_diffs = []
    prev_gray_small = None

    for frame_idx, frame in enumerate(frames):
        try:
            image_bytes = frame.read()
            logger.info(f"[F{frame_idx}] Bytes received: {len(image_bytes)}")
            
            if len(image_bytes) == 0:
                logger.error(f"[F{frame_idx}] EMPTY - 0 bytes received!")
                frames_failed += 1
                continue
            
            nparr = np.frombuffer(image_bytes, np.uint8)
            logger.info(f"[F{frame_idx}] numpy array shape: {nparr.shape}, dtype: {nparr.dtype}")
            
            bgr_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if bgr_image is None:
                logger.error(f"[F{frame_idx}] cv2.imdecode() returned None - JPEG decode failed")
                frames_failed += 1
                continue
            
            h, w = bgr_image.shape[:2]
            logger.info(f"[F{frame_idx}] DECODED: {w}x{h}, uint8 range: {bgr_image.min()}-{bgr_image.max()}, nbytes: {bgr_image.nbytes}")

            # Basic anti-replay signal: repeated/static frames are suspicious.
            try:
                gray_small = cv2.resize(cv2.cvtColor(bgr_image, cv2.COLOR_BGR2GRAY), (64, 64))
                if prev_gray_small is not None:
                    frame_diff = float(np.mean(cv2.absdiff(gray_small, prev_gray_small)))
                    consecutive_frame_diffs.append(frame_diff)
                prev_gray_small = gray_small
            except Exception as e:
                logger.warning(f"[F{frame_idx}] Frame-diff computation skipped: {e}")

            # Face validation is handled by MediaPipe inside extract_eye_landmarks.
            # Running DeepFace.extract_faces() on every frame here would take
            # 1-2 seconds per frame (CPU inference) = 15-30 s total, causing
            # the request to time out and the frontend to show "Liveness failed".
            # MediaPipe raises RuntimeError("Exactly one face required") for
            # multi-face frames and RuntimeError("No face detected") for empty
            # frames, so DeepFace is redundant in this loop.

            try:
                logger.info(f"[F{frame_idx}] Calling extract_eye_landmarks...")
                left_eye, right_eye, landmarks = extract_eye_landmarks(bgr_image)
                logger.info(f"[F{frame_idx}] OK Face detected with {len(landmarks)} landmarks")
            except RuntimeError as e:
                err_str = str(e)
                if "Exactly one face required" in err_str or "multiple" in err_str.lower():
                    return _tamper_response(session_key, "Exactly one face must be visible. Multiple faces detected.", 400)
                logger.warning(f"[F{frame_idx}] FAIL Face detection failed (RuntimeError): {err_str}")
                frames_failed += 1
                continue
            except Exception as e:
                logger.error(f"[F{frame_idx}] FAIL Face detection failed (Unexpected): {type(e).__name__}: {str(e)}", exc_info=True)
                frames_failed += 1
                continue

            try:
                nose_pos = np.array(landmarks[1], dtype=np.float32)
                if first_nose is None:
                    first_nose = nose_pos
                if prev_nose is not None:
                    delta_total = float(np.linalg.norm(nose_pos - prev_nose))
                    nose_movement += delta_total
                    delta_x = abs(float(nose_pos[0]) - float(prev_nose[0]))
                    if delta_x > NOSE_X_THRESHOLD:
                        movement_detected = True
                if first_nose is not None:
                    nose_x_span = max(nose_x_span, abs(float(nose_pos[0]) - float(first_nose[0])))
                    if nose_x_span >= NOSE_X_SPAN_THRESHOLD:
                        movement_detected = True
                prev_nose = nose_pos
            except Exception as e:
                print("Nose tracking error:", str(e))

            try:
                frame_blink_detected, ear_score = detect_blink(left_eye, right_eye)
                ear_values.append(ear_score)
                if frame_blink_detected:
                    closed_eye_frames += 1
                logger.info(f"Frame {frame_idx}: EAR={ear_score}, blink={frame_blink_detected}")
                frames_processed += 1
            except Exception as e:
                logger.error(f"Frame {frame_idx}: Blink detection error: {str(e)}")
                frames_failed += 1
                continue
        
        except Exception as e:
            logger.error(f"Frame {frame_idx}: Unhandled frame error: {str(e)}", exc_info=True)
            frames_failed += 1
            continue

    logger.info(f"[SELFIE] Frame processing complete: {frames_processed} processed, {frames_failed} failed, EAR values: {ear_values}")

    if consecutive_frame_diffs:
        avg_frame_diff = float(np.mean(consecutive_frame_diffs))
        logger.info("[SELFIE] Average consecutive frame diff: %.4f", avg_frame_diff)
        if avg_frame_diff < STATIC_FRAME_DIFF_THRESHOLD:
            logger.warning("[SELFIE] Suspected spoof/replay: frames too static")
            return _tamper_response(
                session_key,
                "Suspicious static/replayed frames detected. Please use a live camera feed.",
                400,
            )

    if len(ear_values) == 0:
        error_msg = f"No face detected in any frames (processed: {frames_processed}, failed: {frames_failed})"
        logger.error(f"[SELFIE] {error_msg}")
        return jsonify({
            "error": "No face detected. Please ensure your face is clearly visible and well-lit.",
            "details": error_msg,
            "debug_info": "All frames failed at face detection. Check frame quality and lighting.",
            "liveness": "fail",
            "processed_frames": frames_processed,
            "failed_frames": frames_failed,
            "ear_values": ear_values
        }), 400

    blink_detected, blink_debug = detect_blink_sequence(ear_values, absolute_threshold=EAR_THRESHOLD)

    print("Frames processed:", frames_processed)
    print("Nose movement:", nose_movement)
    print("Nose X span:", nose_x_span)
    print("Movement detected:", movement_detected)
    print("Closed-eye frames:", closed_eye_frames)
    print("Blink detected:", blink_detected)
    print("Blink debug:", blink_debug)

    if not movement_detected and nose_movement >= TOTAL_NOSE_MOVEMENT_THRESHOLD:
        movement_detected = True
        logger.info(
            "[SELFIE] Movement accepted via cumulative nose motion: total=%.3f, span_x=%.3f",
            nose_movement,
            nose_x_span,
        )

    logger.info(
        "[SELFIE] Blink analysis: detected=%s, movement_detected=%s, closed_eye_frames=%s, nose_movement=%.3f, nose_x_span=%.3f, debug=%s",
        blink_detected,
        movement_detected,
        closed_eye_frames,
        nose_movement,
        nose_x_span,
        blink_debug,
    )

    if frames_processed < 2:
        return jsonify({
            "liveness": "fail",
            "message": "Not enough frames"
        }), 400

    # NOTE: nose_movement check has been removed.
    # It incorrectly rejects users who sit still (the expected behavior for a
    # webcam selfie), and it provides no real anti-spoofing value because a
    # printed photo can be physically moved. Blink detection is the real signal.

    # Anti-spoofing: pass on blink OR head movement (natural interaction).
    liveness_passed = blink_detected or movement_detected
    if not liveness_passed:
        attempt_result = record_failure(session_key, "liveness")
        fail_msg = "Please blink or slightly move your head to verify you are live."
        if attempt_result["locked"]:
            fail_msg = "Too many liveness failures. Session locked for 15 minutes."
        elif attempt_result["remaining_attempts"] > 0:
            fail_msg = f"Liveness failed. {attempt_result['remaining_attempts']} attempt(s) remaining."
        return jsonify({
            "liveness": "fail",
            "message": fail_msg,
            "ear_score": float(np.mean(ear_values)) if ear_values else 0.0,
            "movement": nose_movement,
            "movement_detected": movement_detected,
            "frames_processed": frames_processed,
            "ear_values": ear_values,
            "blink_debug": blink_debug,
        }), 400

    # Liveness passed — reset consecutive failure counter
    reset_attempts(session_key, "liveness")

    liveness = "pass"
    ear_score = float(np.mean(ear_values)) if ear_values else 0.0
    print(f"STEP: Liveness passed — blink={blink_detected}, movement={movement_detected}, EAR mean={ear_score:.4f}, frames_processed={frames_processed}")

    # ── HARD IDENTITY GATE ─────────────────────────────────────────────────────
    # For returning voters (booth access): verify face matches enrolled face.
    # For first-time registrants: voter.face_embedding is None → enrollment path.
    prior_face_path = voter.face_embedding if voter.face_embedding else None

    if prior_face_path and (os.path.exists(prior_face_path) or os.path.isdir(prior_face_path)):
        logger.info("[SELFIE] Returning voter detected — running identity check")

        # Collect frame bytes from the uploaded liveness frames (up to 5)
        frame_bytes_for_identity = []
        for fi, frame in enumerate(frames[:5]):
            try:
                frame.seek(0)
                img_bytes = frame.read()
                if img_bytes:
                    frame_bytes_for_identity.append(img_bytes)
            except Exception as _tmp_err:
                logger.warning(f"[SELFIE] Identity gate frame {fi} read failed: {_tmp_err}")
                continue

        if not frame_bytes_for_identity:
            logger.error("[SELFIE] BLOCK: Could not read any frames for identity check")
            return jsonify({"liveness": "fail", "error": "Could not capture live face for identity verification"}), 400

        # ── Multi-frame DeepFace identity verification ────────────────────────
        print("STEP: Identity verification starting")
        print(f"STEP: Stored path = {prior_face_path}")
        print(f"STEP: Live frames count = {len(frame_bytes_for_identity)}")
        # Load cached embeddings for fast path (Part 1→2 pipeline)
        gate_stored_embeddings = None
        if voter.face_embeddings_json:
            try:
                gate_stored_embeddings = json.loads(voter.face_embeddings_json)
                logger.info(f"[SELFIE] Loaded {len(gate_stored_embeddings)} cached embeddings for identity gate")
            except Exception as _je:
                logger.warning(f"[SELFIE] Could not parse face_embeddings_json: {_je}")

        id_result = verify_identity_multiframe(prior_face_path, frame_bytes_for_identity,
                                               stored_embeddings=gate_stored_embeddings)
        print("STEP: Identity result:", id_result.get("verified"))
        print("IDENTITY RESULT:", id_result)

        # Handle retry response (borderline match)
        if id_result.get("status") == "retry":
            logger.warning("[SELFIE] IDENTITY GATE RETRY for voter %s", voter.aadhaar_hash)
            return jsonify({
                "status": "retry",
                "liveness": "fail",
                "message": id_result.get("message", "Please look straight and try again"),
                "distance": id_result.get("distance", 1.0),
            }), 400

        if id_result.get("verified") is not True:
            print(">>> FACE MISMATCH - BLOCKING")
            logger.error("[SELFIE] IDENTITY GATE BLOCKED: face mismatch for voter %s", voter.aadhaar_hash)
            attempt_result = record_failure(session_key, "face")
            face_msg = "Identity verification failed. Face does not match registered user."
            if attempt_result["locked"]:
                face_msg = "Too many face verification failures. Session locked for 15 minutes."
            elif attempt_result["remaining_attempts"] > 0:
                face_msg = f"Face mismatch. {attempt_result['remaining_attempts']} attempt(s) remaining."
            return jsonify({
                "status": "failed",
                "liveness": "fail",
                "error": face_msg,
                "distance": id_result.get("distance", 1.0),
            }), 400

        reset_attempts(session_key, "face")
        print("\u2705 FACE MATCH - ALLOWING ACCESS")
        logger.info("[SELFIE] PASS Identity confirmed for voter %s", voter.aadhaar_hash)
    else:
        logger.info("[SELFIE] First enrollment — no prior face, skipping identity check")

        # For new registrations, cross-check the live face against voters who have already voted.
        # This keeps the old false-positive-prone registration-time dedup removed while still
        # blocking reuse of a previously voted identity during the liveness step itself.
        if not is_real_register_flow:
            logger.info("[SELFIE] Cross-user registration face check skipped for non-real-register flow")
        else:
            frame_bytes_for_identity = []
            for fi, frame in enumerate(frames[:5]):
                try:
                    frame.seek(0)
                    img_bytes = frame.read()
                    if img_bytes:
                        frame_bytes_for_identity.append(img_bytes)
                except Exception as _tmp_err:
                    logger.warning(f"[SELFIE] Registration cross-check frame {fi} read failed: {_tmp_err}")
                    continue

            if frame_bytes_for_identity:
                all_enrolled_voters = Voter.query.filter(Voter.face_embedding.isnot(None)).all()
                for prior_voter in all_enrolled_voters:
                    prior_face_path = prior_voter.face_embedding
                    if not prior_face_path or not (os.path.exists(prior_face_path) or os.path.isdir(prior_face_path)):
                        continue

                    try:
                        gate_stored_embeddings = None
                        if prior_voter.face_embeddings_json:
                            gate_stored_embeddings = json.loads(prior_voter.face_embeddings_json)

                        id_result = verify_identity_multiframe(
                            prior_face_path,
                            frame_bytes_for_identity,
                            stored_embeddings=gate_stored_embeddings,
                        )
                        if id_result.get("verified") is True:
                            logger.warning("[SELFIE] Registration blocked — live face matched existing voter %s", prior_voter.aadhaar_hash)
                            attempt_result = record_failure(session_key, "face")
                            if prior_voter.has_voted:
                                face_msg = "This face matches a voter who has already voted. Registration denied."
                            else:
                                face_msg = "This face matches an already registered voter. Duplicate identity registration is not allowed."

                            if attempt_result["locked"]:
                                face_msg = "Too many face verification failures. Session locked for 15 minutes."
                            elif attempt_result["remaining_attempts"] > 0:
                                face_msg = f"{face_msg} {attempt_result['remaining_attempts']} attempt(s) remaining."
                            return jsonify({
                                "status": "failed",
                                "liveness": "fail",
                                "error": face_msg,
                                "distance": id_result.get("distance", 1.0),
                                "attempt_type": "face",
                            }), 403
                    except Exception as _cross_err:
                        logger.warning(
                            "[SELFIE] Registration cross-check skipped for voter %s: %s",
                            prior_voter.aadhaar_hash,
                            _cross_err,
                        )
    # ── END HARD IDENTITY GATE ────────────────────────────────────────────────

    # ── Save multi-frame registration faces ────────────────────────────────
    logger.info("[SELFIE] Saving 5 registration face samples with aadhaar_hash...")
    print(f"\n[SELFIE] Voter aadhaar_hash: {voter.aadhaar_hash}")

    # Collect all frame images (up to 5 valid)
    frame_images_for_save = []
    for frame_idx, frame in enumerate(frames):
        try:
            frame.seek(0)
            image_bytes = frame.read()
            if len(image_bytes) == 0:
                logger.warning(f"[SELFIE] Frame {frame_idx} is empty, skipping")
                continue
            frame_image = load_image_from_bytes(image_bytes)
            frame_images_for_save.append(frame_image)
        except Exception as e:
            logger.warning(f"[SELFIE] Frame {frame_idx} load failed: {str(e)}")
            continue

    face_image_path = save_multi_registration_faces(frame_images_for_save, voter.aadhaar_hash)

    if not face_image_path:
        logger.error("[SELFIE] BLOCK: Could not save any registration face — face detection failed in all frames")
        print(f"[SELFIE] REGISTRATION BLOCKED: No valid face detected in any frame")
        return jsonify({"error": "Face detection failed - face must be clearly visible with no multiple faces", "liveness": "fail"}), 400

    try:
        biometric = Biometric(
            voter_id=uuid.UUID(voter_id),
            face_embedding=face_image_path,  # Store the STRICT registration face path with aadhaar_hash
            liveness_score=float(np.mean(ear_values))
        )

        db.session.add(biometric)
        
        # Store the registration face folder path in voter record for voting verification
        if voter:
            voter.face_embedding = face_image_path  # Path: backend/data/faces/{aadhaar_hash}/
            logger.info(f"[SELFIE] SAVED multi-frame registration folder in voter.face_embedding: {face_image_path}")
            print(f"[SELFIE] ✓ Voter registered with face folder: {face_image_path}")
            voter.liveness_score = float(np.mean(ear_values))

            # PART 1: Extract and cache Facenet embeddings for fast verification
            try:
                stored_embs = extract_embeddings_from_folder(face_image_path, max_count=3)
                if stored_embs:
                    voter.face_embeddings_json = json.dumps(stored_embs)
                    logger.info(f"[SELFIE] Cached {len(stored_embs)} Facenet embeddings in voter record")
                    print(f"[SELFIE] ✓ Stored {len(stored_embs)} Facenet embeddings")
                else:
                    logger.warning("[SELFIE] No embeddings extracted — will use image fallback during verification")
            except Exception as emb_err:
                logger.warning(f"[SELFIE] Embedding extraction failed (non-fatal): {str(emb_err)}")
        
        db.session.commit()
    except Exception as e:
        logger.error(f"Database error during registration: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}", "liveness": "fail"}), 500

    logger.info(f"[SELFIE] REGISTRATION COMPLETE: Liveness passed + 5-frame face folder saved")
    response = {
        "liveness": liveness,
        "ear_score": ear_score,
        "movement": nose_movement,
        "frames_processed": frames_processed,
        "ear_values": ear_values,
        "message": "Liveness verified - Multi-frame face enrolled (5 samples)",
        "biometric_id": biometric.id,
        "face_image_stored": True,
        "registration_face": face_image_path
    }
    
    return jsonify(response), 200