import io
import json
import uuid
import numpy as np
from flask import Blueprint, request, jsonify
from PIL import Image

# face_recognition relies on dlib and cmake at build time; ensure it's available
try:
    import face_recognition
except ImportError as ie:
    raise RuntimeError("face_recognition library is required for accurate EAR detection. "
                       "Install via pip ensuring cmake and dlib are present.") from ie

from app.db import db
from app.models import Biometric
from app.services.liveness import detect_blink

bp = Blueprint("biometrics", __name__, url_prefix="/api/biometrics")


def load_image_from_bytes(image_bytes):
    """Load PIL Image from bytes and convert to RGB."""
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image


def extract_eye_landmarks(image_array):
    """
    Obtain exact eyelid landmarks via face_recognition.
    
    Returns (left_eye, right_eye) as numpy arrays or None on failure.
    """
    # face_recognition works with RGB numpy arrays directly
    landmarks_list = face_recognition.face_landmarks(image_array)
    if not landmarks_list:
        return None
    landmarks = landmarks_list[0]
    left = landmarks.get("left_eye")
    right = landmarks.get("right_eye")
    if not left or not right:
        return None
    return np.array(left, dtype=np.float32), np.array(right, dtype=np.float32)



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
        schema:
          type: object
          properties:
            liveness:
              type: string
              example: pass
            ear_score:
              type: number
              example: 0.32
            biometric_id:
              type: integer
      400:
        description: Liveness check failed or invalid input
        schema:
          type: object
          properties:
            liveness:
              type: string
              example: fail
            ear_score:
              type: number
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
        # use face_recognition to load image for consistency
        image = face_recognition.load_image_file(io.BytesIO(image_bytes))
        image_array = np.array(image)

        landmarks = face_recognition.face_landmarks(image_array)
        if not landmarks:
            return jsonify(
                {"liveness": "fail", "ear_score": 0.0, "message": "No face detected"}
            ), 400
        face_landmarks = landmarks[0]
        left_eye = face_landmarks.get("left_eye")
        right_eye = face_landmarks.get("right_eye")
        if not left_eye or not right_eye:
            return jsonify(
                {"liveness": "fail", "ear_score": 0.0, "message": "Eye landmarks missing"}
            ), 400

        left_eye_arr = np.array(left_eye, dtype=np.float32)
        right_eye_arr = np.array(right_eye, dtype=np.float32)
        blink_detected, ear_score = detect_blink(left_eye_arr, right_eye_arr)
        if not blink_detected:
            return jsonify(
                {
                    "liveness": "fail",
                    "ear_score": ear_score,
                    "message": "No blink detected; liveness verification failed",
                }
            ), 400

        # embedding from face_recognition
        encodings = face_recognition.face_encodings(image_array)
        if not encodings:
            return jsonify(
                {"liveness": "fail", "ear_score": ear_score, "message": "Unable to compute embedding"}
            ), 400
        embedding = encodings[0]
        embedding_json = json.dumps(embedding.tolist())

        biometric = Biometric(
            voter_id=uuid.UUID(voter_id_str),
            face_embedding=embedding_json,
            liveness_score=float(ear_score),
        )
        db.session.add(biometric)
        db.session.commit()

        return jsonify(
            {
                "liveness": "pass",
                "ear_score": ear_score,
                "message": "Liveness verification successful",
                "biometric_id": biometric.id,
            }
        ), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Processing error: {str(e)}"}), 500
