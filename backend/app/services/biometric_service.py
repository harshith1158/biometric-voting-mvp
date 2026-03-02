import io
import json
import numpy as np
import cv2
import face_recognition
from PIL import Image


def load_image_from_bytes(image_bytes):
    """Load PIL Image from bytes."""
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image


def detect_faces(image):
    """Detect faces in image using face_recognition.
    
    Returns list of face locations as (top, right, bottom, left) tuples.
    """
    image_array = np.array(image)
    face_locations = face_recognition.face_locations(image_array, model="hog")
    return face_locations


def compute_eye_aspect_ratio(shape, eye_indices):
    """Compute Eye Aspect Ratio (EAR) for given eye landmarks.
    
    EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
    
    Returns float EAR value.
    """
    if len(shape) < 6:
        return 1.0
    
    points = [shape[i] for i in eye_indices]
    if len(points) < 6:
        return 1.0
    
    p1 = np.array(points[0])
    p2 = np.array(points[1])
    p3 = np.array(points[2])
    p4 = np.array(points[3])
    p5 = np.array(points[4])
    p6 = np.array(points[5])
    
    numerator = np.linalg.norm(p2 - p6) + np.linalg.norm(p3 - p5)
    denominator = 2.0 * np.linalg.norm(p1 - p4)
    
    if denominator == 0:
        return 1.0
    
    ear = numerator / denominator
    return ear


def detect_blink(image):
    """Detect blink using Eye Aspect Ratio (EAR).
    
    If EAR < 0.25 at any frame, treat as blink detected.
    Returns (blink_detected: bool, ear_min: float).
    """
    try:
        image_array = np.array(image)
        face_landmarks_list = face_recognition.face_landmarks(image_array)
        
        if not face_landmarks_list:
            return False, 1.0
        
        face_landmarks = face_landmarks_list[0]
        
        left_eye = face_landmarks.get("left_eye", [])
        right_eye = face_landmarks.get("right_eye", [])
        
        if not left_eye or not right_eye:
            return False, 1.0
        
        left_eye_array = np.array(left_eye)
        right_eye_array = np.array(right_eye)
        
        left_ear = compute_eye_aspect_ratio(left_eye_array, list(range(len(left_eye))))
        right_ear = compute_eye_aspect_ratio(right_eye_array, list(range(len(right_eye))))
        
        ear_min = min(left_ear, right_ear)
        blink_detected = ear_min < 0.25
        
        return blink_detected, ear_min
    except Exception:
        return False, 1.0


def extract_face_embedding(image):
    """Extract face embedding (128-D vector) from image.
    
    Returns serialized JSON string of embedding.
    """
    try:
        image_array = np.array(image)
        face_locations = face_recognition.face_locations(image_array, model="hog")
        
        if not face_locations:
            return None
        
        encodings = face_recognition.face_encodings(image_array, face_locations)
        
        if not encodings:
            return None
        
        embedding = encodings[0]
        embedding_json = json.dumps(embedding.tolist())
        
        return embedding_json
    except Exception:
        return None


def store_biometric_data(voter_id, face_embedding, liveness_score):
    """Store biometric data in database.
    
    Args:
        voter_id: UUID of voter
        face_embedding: JSON string of face embedding
        liveness_score: float (0.0 or 1.0 for PASS/FAIL)
    
    Returns:
        BiometricData instance or None on failure.
    """
    try:
        from app.models import BiometricData
        from app.db import db
        
        biometric = BiometricData(
            voter_id=voter_id,
            face_embedding=face_embedding,
            liveness_score=liveness_score,
        )
        db.session.add(biometric)
        db.session.commit()
        
        return biometric
    except Exception as e:
        return None


def process_selfie(voter_id, image_bytes):
    """End-to-end selfie processing: detect, blink check, embed, store.
    
    Returns dict with status, liveness_result, embedding_stored, error.
    """
    try:
        image = load_image_from_bytes(image_bytes)
    except Exception as e:
        return {
            "status": "error",
            "error": "Invalid image format",
            "liveness_result": None,
            "embedding_stored": False,
        }
    
    face_locations = detect_faces(image)
    if not face_locations:
        return {
            "status": "error",
            "error": "No face detected",
            "liveness_result": None,
            "embedding_stored": False,
        }
    
    blink_detected, ear_min = detect_blink(image)
    liveness_result = "PASS" if blink_detected else "FAIL"
    liveness_score = 1.0 if blink_detected else 0.0
    
    face_embedding = extract_face_embedding(image)
    if not face_embedding:
        return {
            "status": "error",
            "error": "Failed to extract face embedding",
            "liveness_result": liveness_result,
            "embedding_stored": False,
        }
    
    stored = store_biometric_data(voter_id, face_embedding, liveness_score)
    
    return {
        "status": "success",
        "liveness_result": liveness_result,
        "embedding_stored": stored is not None,
        "ear_min": float(ear_min),
    }
