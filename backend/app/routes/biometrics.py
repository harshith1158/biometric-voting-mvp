from flask import Blueprint, request, jsonify
import numpy as np
import cv2
import uuid
import json

from app.db import db
from app.models import Biometric
from app.services.liveness import detect_blink
from app.routes.landmarks import extract_eye_landmarks   # if your helper exists

bp = Blueprint("biometrics", __name__, url_prefix="/api/biometrics")

EAR_THRESHOLD = 0.25
MIN_BLINK_FRAMES = 2


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

    if "frames" not in request.files:
        return jsonify({"error": "No frames uploaded"}), 400

    voter_id = request.form.get("voter_id")
    if not voter_id:
        return jsonify({"error": "voter_id missing"}), 400

    try:
        uuid.UUID(voter_id)
    except:
        return jsonify({"error": "invalid voter_id"}), 400

    frames = request.files.getlist("frames")

    if len(frames) < 3:
        return jsonify({"error": "Minimum 3 frames required"}), 400

    ear_values = []
    embedding_vector = None

    for frame in frames:

        image_bytes = frame.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if bgr_image is None:
            continue

        try:
            left_eye, right_eye, landmarks = extract_eye_landmarks(bgr_image)
        except:
            continue

        blink_detected, ear_score = detect_blink(left_eye, right_eye)

        ear_values.append(ear_score)

        if embedding_vector is None:
            vect = []
            for i in range(min(50, len(landmarks))):
                lm = landmarks[i]

                if hasattr(lm, "x"):
                    vect.extend([lm.x, lm.y])
                else:
                    vect.extend([lm[0], lm[1]])

            embedding_vector = np.array(vect, dtype=np.float32)

    if len(ear_values) == 0:
        return jsonify({"error": "No face detected"}), 400

    blink_frames = 0
    for ear in ear_values:
        if ear < EAR_THRESHOLD:
            blink_frames += 1

    if blink_frames < MIN_BLINK_FRAMES:
        return jsonify({
            "liveness": "fail",
            "ear_values": ear_values,
            "message": "Blink not detected"
        }), 400

    embedding_vector = embedding_vector / np.linalg.norm(embedding_vector)

    biometric = Biometric(
        voter_id=uuid.UUID(voter_id),
        face_embedding=json.dumps(embedding_vector.tolist()),
        liveness_score=float(np.mean(ear_values))
    )

    db.session.add(biometric)
    db.session.commit()

    return jsonify({
        "liveness": "pass",
        "ear_values": ear_values,
        "message": "Blink detected",
        "biometric_id": biometric.id
    }), 200