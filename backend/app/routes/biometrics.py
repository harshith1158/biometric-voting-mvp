import io
import json
import uuid
import numpy as np
from flask import Blueprint, request, jsonify
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python import BaseOptions

from app.db import db
from app.models import Biometric
from app.services.liveness import detect_blink

bp = Blueprint("biometrics", __name__, url_prefix="/api/biometrics")

# constants for eye landmark indices (MediaPipe FaceMesh topology)
LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


def extract_eye_landmarks(bgr_image: np.ndarray):
    """Run FaceLandmarker on a BGR image and return eye landmarks and full mesh."""
    image_height, image_width = bgr_image.shape[:2]

    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)

    mp_image = mp.Image(
        image_format=mp.ImageFormat.SRGB,
        data=rgb_image
    )

    result = face_landmarker.detect(mp_image)

    faces = result.face_landmarks
    if not faces:
        raise ValueError("No face detected")

    landmarks = faces[0]

    def to_pixel(lm):
        return np.array([
            int(lm.x * image_width),
            int(lm.y * image_height)
        ], dtype=np.float32)

    left_eye = np.array([to_pixel(landmarks[i]) for i in LEFT_EYE], dtype=np.float32)
    right_eye = np.array([to_pixel(landmarks[i]) for i in RIGHT_EYE], dtype=np.float32)

    return left_eye, right_eye, landmarks


# Initialize FaceLandmarker once at module level
from pathlib import Path
import os

_model_path = os.environ.get('MEDIAPIPE_MODEL_PATH') or str(
    Path(__file__).resolve().parents[1] / 'models' / 'face_landmarker.task'
)

base_options = BaseOptions(model_asset_path=_model_path)

options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=False,
    num_faces=1,
)

face_landmarker = vision.FaceLandmarker.create_from_options(options)


@bp.route("/selfie", methods=["POST"])
def selfie_liveness():
    """
    Verify biometric liveness from a selfie image.
    ---
    tags:
      - Biometrics
    summary: Selfie-based liveness verification
    description: >
      Accept a selfie image, detect face and eyes, compute Eye Aspect Ratio (EAR)
      for blink detection. If blink detected, store face embedding and liveness score.
      Raw images are NOT stored.
    parameters:
      - name: image
        in: formData
        type: file
        required: true
        description: Selfie image (JPEG or PNG)
      - name: voter_id
        in: formData
        type: string
        required: true
        description: UUID of the voter
    responses:
      200:
        description: Liveness verification passed
      400:
        description: Liveness check failed or invalid input
      500:
        description: Processing error
    """

    if "image" not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    if "voter_id" not in request.form:
        return jsonify({"error": "voter_id is required"}), 400

    voter_id_str = request.form.get("voter_id")
    image_file = request.files["image"]

    if image_file.filename == "":
        return jsonify({"error": "Image file is empty"}), 400

    try:
        uuid.UUID(voter_id_str)
    except ValueError:
        return jsonify({"error": "Invalid voter_id format"}), 400

    try:
        image_bytes = image_file.read()
        nparr = np.frombuffer(image_bytes, np.uint8)
        bgr_image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if bgr_image is None:
            return jsonify({"error": "Invalid image data"}), 400

        try:
            left_eye, right_eye, landmarks = extract_eye_landmarks(bgr_image)
        except ValueError as ve:
            return jsonify({
                "liveness": "fail",
                "ear_score": 0.0,
                "message": f"Face detection error: {ve}"
            }), 400

        blink_detected, ear_score = detect_blink(left_eye, right_eye)

        if not blink_detected:
            return jsonify({
                "liveness": "fail",
                "ear_score": ear_score,
                "message": "No blink detected; liveness verification failed"
            }), 400

        vect = []

        for i in range(min(50, len(landmarks))):
            lm = landmarks[i]
            vect.extend([lm.x, lm.y])

        embedding = np.array(vect, dtype=np.float32)

        if embedding.size == 0 or np.linalg.norm(embedding) == 0:
            return jsonify({
                "liveness": "fail",
                "ear_score": ear_score,
                "message": "Embedding zero"
            }), 400

        embedding = embedding / np.linalg.norm(embedding)
        embedding_json = json.dumps(embedding.tolist())

        biometric = Biometric(
            voter_id=uuid.UUID(voter_id_str),
            face_embedding=embedding_json,
            liveness_score=float(ear_score),
        )

        db.session.add(biometric)
        db.session.commit()

        return jsonify({
            "liveness": "pass",
            "ear_score": ear_score,
            "message": "Liveness verification successful",
            "biometric_id": biometric.id,
        }), 200

    except Exception as e:
        import traceback
        traceback.print_exc()

        return jsonify({
            "error": "Processing error",
            "details": str(e)
        }), 500