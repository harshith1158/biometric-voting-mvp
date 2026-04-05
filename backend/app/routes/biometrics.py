from flask import Blueprint, request, jsonify
import uuid
import json
import logging

from app.db import db
from app.models import Biometric, Voter
from app.services.liveness import detect_blink
from app.routes.landmarks import extract_eye_landmarks

logger = logging.getLogger(__name__)

bp = Blueprint("biometrics", __name__, url_prefix="/api/biometrics")

EAR_THRESHOLD = 0.25
MIN_BLINK_FRAMES = 2
FACE_DUPLICATE_THRESHOLD = 0.98


def cosine_similarity(a, b):
  import numpy as np
  denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
  if denominator == 0.0:
    return 0.0
  return float(np.dot(a, b) / denominator)


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
    
    logger.info(f"[SELFIE] voter_id: {voter_id}")

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

    frames = request.files.getlist("frames")
    logger.info(f"[SELFIE] Received {len(frames)} frames")

    if len(frames) < 3:
        return jsonify({"error": "Minimum 3 frames required"}), 400

    ear_values = []
    embedding_vector = None
    frames_processed = 0
    frames_failed = 0
    prev_nose = None
    nose_movement = 0.0
    blink_detected = False

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

            try:
                logger.info(f"[F{frame_idx}] Calling extract_eye_landmarks...")
                left_eye, right_eye, landmarks = extract_eye_landmarks(bgr_image)
                logger.info(f"[F{frame_idx}] ✓ Face detected with {len(landmarks)} landmarks")
            except RuntimeError as e:
                if "Exactly one face required" in str(e):
                    return jsonify({"liveness": "fail", "message": "Exactly one face required"}), 400
                logger.warning(f"[F{frame_idx}] ✗ Face detection failed (RuntimeError): {str(e)}")
                frames_failed += 1
                continue
            except Exception as e:
                logger.error(f"[F{frame_idx}] ✗ Face detection failed (Unexpected): {type(e).__name__}: {str(e)}", exc_info=True)
                frames_failed += 1
                continue

            try:
                nose_pos = np.array(landmarks[1], dtype=np.float32)
                if prev_nose is not None:
                    nose_movement += float(np.linalg.norm(nose_pos - prev_nose))
                prev_nose = nose_pos
            except Exception as e:
                print("Nose tracking error:", str(e))

            try:
                frame_blink_detected, ear_score = detect_blink(left_eye, right_eye)
                ear_values.append(ear_score)
                if frame_blink_detected:
                    blink_detected = True
                logger.info(f"Frame {frame_idx}: EAR={ear_score}, blink={frame_blink_detected}")
                frames_processed += 1
            except Exception as e:
                logger.error(f"Frame {frame_idx}: Blink detection error: {str(e)}")
                frames_failed += 1
                continue

            if embedding_vector is None and landmarks:
                try:
                    vect = []
                    for i in range(min(50, len(landmarks))):
                        lm = landmarks[i]

                        if hasattr(lm, "x"):
                            vect.extend([lm.x, lm.y])
                        else:
                            vect.extend([lm[0], lm[1]])

                    embedding_vector = np.array(vect, dtype=np.float32)
                    logger.info(f"Frame {frame_idx}: Embedding extracted ({len(vect)} values)")
                except Exception as e:
                    logger.error(f"Frame {frame_idx}: Embedding extraction failed: {str(e)}")
        
        except Exception as e:
            logger.error(f"Frame {frame_idx}: Unhandled frame error: {str(e)}", exc_info=True)
            frames_failed += 1
            continue

    logger.info(f"[SELFIE] Frame processing complete: {frames_processed} processed, {frames_failed} failed, EAR values: {ear_values}")

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

    print("Frames processed:", frames_processed)
    print("Nose movement:", nose_movement)
    print("Blink detected:", blink_detected)

    if frames_processed < 2:
        return jsonify({
            "liveness": "fail",
            "message": "Not enough frames"
        }), 400

    if nose_movement < 5:
        return jsonify({
            "liveness": "fail",
            "message": "Face not stable"
        }), 400

    liveness = "pass" if (nose_movement >= 5 or blink_detected) else "fail"
    ear_score = float(np.mean(ear_values)) if ear_values else 0.0

    if liveness == "fail":
        return jsonify({
            "liveness": "fail",
            "message": "Liveness not detected",
            "ear_score": ear_score,
            "movement": nose_movement,
            "frames_processed": frames_processed,
            "ear_values": ear_values
        }), 400

    # Validate and normalize embedding vector
    if embedding_vector is None:
        logger.error("Embedding vector is None")
        return jsonify({"error": "Could not extract embedding", "liveness": "fail"}), 400
    
    embedding_norm = np.linalg.norm(embedding_vector)
    if embedding_norm <= 0:
        logger.error(f"Invalid embedding norm: {embedding_norm}")
        return jsonify({"error": "Invalid embedding", "liveness": "fail"}), 400
    
    embedding_vector = embedding_vector / embedding_norm

    print("Checking face similarity")
    biometrics = Biometric.query.all()
    for existing in biometrics:
      try:
        # Allow re-enrollment retries for the same voter without duplicate blocking.
        if existing.voter_id == voter_uuid:
          continue

        stored = np.array(json.loads(existing.face_embedding), dtype=np.float32)
        if stored.size == 0 or stored.shape != embedding_vector.shape:
          logger.warning(
            f"[SELFIE] Skipping biometric id {existing.id}: invalid shape {stored.shape}"
          )
          continue

        similarity = cosine_similarity(embedding_vector, stored)
        if not np.isfinite(similarity):
          logger.warning(f"[SELFIE] Skipping biometric id {existing.id}: non-finite similarity")
          continue

        print("Checking face similarity:", similarity)
        print("Face similarity:", similarity)
        if similarity > FACE_DUPLICATE_THRESHOLD:
          print("Duplicate face detected")
          return jsonify({"error": "Face already registered"}), 400
      except Exception as e:
        logger.warning(f"[SELFIE] Failed to compare with biometric id {existing.id}: {str(e)}")

    try:
        biometric = Biometric(
            voter_id=uuid.UUID(voter_id),
            face_embedding=json.dumps(embedding_vector.tolist()),
            liveness_score=float(np.mean(ear_values))
        )

        db.session.add(biometric)
        db.session.commit()
    except Exception as e:
        logger.error(f"Database error: {str(e)}", exc_info=True)
        db.session.rollback()
        return jsonify({"error": f"Database error: {str(e)}", "liveness": "fail"}), 500

    logger.info(f"[SELFIE] ✓ LIVENESS PASSED for voter {voter_id}")
    return jsonify({
        "liveness": liveness,
        "ear_score": ear_score,
        "movement": nose_movement,
        "frames_processed": frames_processed,
        "ear_values": ear_values,
        "message": "Liveness verified - Biometric enrolled",
        "biometric_id": biometric.id
    }), 200