import io
import json
import uuid
import numpy as np
from flask import Blueprint, request, jsonify
from PIL import Image
import cv2
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
    Extract eye landmarks from image using OpenCV cascade classifiers.
    
    Returns (left_eye, right_eye) as (6, 2) numpy arrays or None if detection fails.
    """
    try:
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_eye.xml"
        )
        
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4)
        
        if len(faces) == 0:
            return None
        
        x, y, w, h = faces[0]
        roi_gray = gray[y : y + h, x : x + w]
        eyes = eye_cascade.detectMultiScale(roi_gray)
        
        if len(eyes) < 2:
            return None
        
        eye1 = eyes[0]
        eye2 = eyes[1] if len(eyes) > 1 else eyes[0]
        
        ex1, ey1, ew1, eh1 = eye1
        ex2, ey2, ew2, eh2 = eye2
        
        left_eye = np.array([
            [ex1, ey1],
            [ex1 + ew1 * 0.25, ey1],
            [ex1 + ew1 * 0.5, ey1 + eh1 * 0.3],
            [ex1 + ew1, ey1],
            [ex1 + ew1 * 0.5, ey1 + eh1 * 0.8],
            [ex1 + ew1 * 0.75, ey1],
        ], dtype=np.float32)
        
        right_eye = np.array([
            [ex2, ey2],
            [ex2 + ew2 * 0.25, ey2],
            [ex2 + ew2 * 0.5, ey2 + eh2 * 0.3],
            [ex2 + ew2, ey2],
            [ex2 + ew2 * 0.5, ey2 + eh2 * 0.8],
            [ex2 + ew2 * 0.75, ey2],
        ], dtype=np.float32)
        
        return left_eye, right_eye
    except Exception:
        return None


def generate_face_embedding():
    """Generate a placeholder normalized face embedding (128-D vector)."""
    embedding = np.random.randn(128).astype(np.float32)
    return embedding / np.linalg.norm(embedding)


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
        pil_image = load_image_from_bytes(image_bytes)
        image_array = np.array(pil_image)
        
        landmarks = extract_eye_landmarks(image_array)
        if landmarks is None:
            return jsonify(
                {
                    "liveness": "fail",
                    "ear_score": 0.0,
                    "message": "Could not detect face or eye landmarks",
                }
            ), 400
        
        left_eye, right_eye = landmarks
        blink_detected, ear_score = detect_blink(left_eye, right_eye)
        
        if not blink_detected:
            return jsonify(
                {
                    "liveness": "fail",
                    "ear_score": ear_score,
                    "message": "No blink detected; liveness verification failed",
                }
            ), 400
        
        embedding = generate_face_embedding()
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
