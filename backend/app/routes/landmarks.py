"""
Extract facial landmarks using MediaPipe FaceMesh.
"""
import numpy as np
import cv2
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from pathlib import Path


def extract_eye_landmarks(bgr_image):
    """
    Extract eye landmarks from an image using MediaPipe FaceMesh.
    
    Args:
        bgr_image: BGR image as numpy array (OpenCV format)
    
    Returns:
        tuple: (left_eye_landmarks, right_eye_landmarks, all_landmarks)
            - left_eye_landmarks: (6, 2) numpy array for left eye
            - right_eye_landmarks: (6, 2) numpy array for right eye
            - all_landmarks: list of all 468 face landmarks
    
    Raises:
        Exception: If no face detected or landmark extraction fails
    """
    if bgr_image is None:
        raise Exception("Invalid image input")
    
    # Convert BGR to RGB
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    h, w = rgb_image.shape[:2]
    
    # Load MediaPipe FaceMesh model
    model_path = Path(__file__).resolve().parents[1] / 'models' / 'face_landmarker.task'
    
    base_options = python.BaseOptions(model_asset_path=str(model_path))
    options = vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False
    )
    detector = vision.FaceLandmarker.create_from_options(options)
    
    # Create MediaPipe Image
    mp_image = vision.Image(image_format=vision.ImageFormat.SRGB, data=rgb_image)
    
    # Detect landmarks
    detection_result = detector.detect(mp_image)
    
    if not detection_result.face_landmarks:
        raise Exception("No face detected in image")
    
    landmarks = detection_result.face_landmarks[0]
    
    # Left eye: indices 263, 362, 386, 374, 380, 381
    # Right eye: indices 33, 160, 158, 133, 153, 144
    left_eye_indices = [263, 362, 386, 374, 380, 381]
    right_eye_indices = [33, 160, 158, 133, 153, 144]
    
    left_eye = np.array([
        [landmarks[i].x * w, landmarks[i].y * h] for i in left_eye_indices
    ], dtype=np.float32)
    
    right_eye = np.array([
        [landmarks[i].x * w, landmarks[i].y * h] for i in right_eye_indices
    ], dtype=np.float32)
    
    # Convert all landmarks to (x, y) pixel coordinates
    all_landmarks_list = []
    for lm in landmarks:
        all_landmarks_list.append([lm.x * w, lm.y * h])
    
    return left_eye, right_eye, all_landmarks_list
