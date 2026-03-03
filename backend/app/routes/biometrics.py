import io
import json
import uuid
import numpy as np
from flask import Blueprint, request, jsonify
from PIL import Image
import cv2

# Require MediaPipe; do not allow Haar-cascade fallback at runtime.
mp = None
face_mesh = None
try:
    import mediapipe as mp
    # initialize MediaPipe face mesh once at module import for reuse
    mp_face_mesh = mp.solutions.face_mesh
    face_mesh = mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
    )
except Exception as e:
    # Fail fast: MediaPipe MUST be available for this application.
    raise RuntimeError(
        "MediaPipe is required for biometric landmarking. "
        "Install the `mediapipe` package in your Python environment (e.g. in venv311) "
        "and restart the server. Example: `python -m pip install mediapipe`"
    ) from e

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
    Extract eye contours; prefer MediaPipe Face Mesh if available,
    otherwise fall back to Haar cascade bounding boxes.
    """
    if face_mesh is not None:
        rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        if not results.multi_face_landmarks:
            return None
        landmarks = results.multi_face_landmarks[0].landmark
        h, w, _ = image_array.shape
        left_idx = [33, 160, 158, 133, 153, 144]
        right_idx = [362, 385, 387, 263, 373, 380]
        def coords(indices):
            pts = []
            for i in indices:
                lm = landmarks[i]
                x_px = int(lm.x * w)
                y_px = int(lm.y * h)
                pts.append([x_px, y_px])
            return np.array(pts, dtype=np.float32)
        return coords(left_idx), coords(right_idx)
    # fallback to Haar cascades (same code as before)
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
        # load image via cv2 for mediapipe
        nparr = np.frombuffer(image_bytes, np.uint8)
        image_array = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image_array is None:
            return jsonify({"error": "Invalid image data"}), 400

        eyes = extract_eye_landmarks(image_array)
        if eyes is None:
            return jsonify({"liveness": "fail", "ear_score": 0.0, "message": "No face detected"}), 400
        left_eye_arr, right_eye_arr = eyes
        blink_detected, ear_score = detect_blink(left_eye_arr, right_eye_arr)
        if not blink_detected:
            return jsonify({
                "liveness": "fail",
                "ear_score": ear_score,
                "message": "No blink detected; liveness verification failed",
            }), 400

        # create embedding from first 50 face_mesh landmarks
        rgb = cv2.cvtColor(image_array, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)
        mesh = results.multi_face_landmarks[0].landmark
        vect = []
        for i in range(min(50, len(mesh))):
            lm = mesh[i]
            vect.extend([lm.x, lm.y])
        embedding = np.array(vect, dtype=np.float32)
        if np.linalg.norm(embedding) == 0:
            return jsonify({"liveness": "fail", "ear_score": ear_score, "message": "Embedding zero"}), 400
        embedding = embedding / np.linalg.norm(embedding)
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
