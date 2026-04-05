"""
Standalone MediaPipe webcam test (Step 11).

Captures a single frame from the default webcam, runs MediaPipe FaceLandmarker
detection on it, and prints the number of faces detected.

Run from the backend/ directory with the project venv activated:
    python test_mediapipe_camera.py

Expected output when a face is visible:
    MODEL PATH: <path>
    MODEL EXISTS: True
    Captured frame: 480x640, dtype=uint8
    Converted to RGB
    MediaPipe image created
    Faces detected: 1
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path

# ── Model path ─────────────────────────────────────────────────────────────────
_model_path = Path(__file__).resolve().parent / 'app' / 'models' / 'face_landmarker.task'
print(f"MODEL PATH: {_model_path}")
print(f"MODEL EXISTS: {_model_path.exists()}")

if not _model_path.exists():
    print("ERROR: Model file not found. Cannot continue.")
    sys.exit(1)

# ── Capture one webcam frame ───────────────────────────────────────────────────
cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("ERROR: Cannot open webcam (index 0). Is a camera connected?")
    sys.exit(1)

ret, frame = cap.read()
cap.release()

if not ret or frame is None:
    print("ERROR: Failed to capture frame from webcam.")
    sys.exit(1)

h, w = frame.shape[:2]
print(f"Captured frame: {h}x{w}, dtype={frame.dtype}")

# ── RGB conversion ─────────────────────────────────────────────────────────────
rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
rgb_image = np.ascontiguousarray(rgb_image.astype(np.uint8))
print("Converted to RGB")

# ── Load MediaPipe model ───────────────────────────────────────────────────────
try:
    from mediapipe.tasks import python as mp_python
    from mediapipe.tasks.python import vision as mp_vision
    from mediapipe.tasks.python.vision.core.image import Image as mp_Image
    from mediapipe import ImageFormat

    base_options = mp_python.BaseOptions(model_asset_path=str(_model_path))
    options = mp_vision.FaceLandmarkerOptions(
        base_options=base_options,
        output_face_blendshapes=False,
    )
    detector = mp_vision.FaceLandmarker.create_from_options(options)
    print("MediaPipe model loaded")
except Exception as e:
    print(f"ERROR: Failed to load MediaPipe model: {type(e).__name__}: {e}")
    sys.exit(1)

# ── Create mp.Image ────────────────────────────────────────────────────────────
try:
    mp_image = mp_Image(image_format=ImageFormat.SRGB, data=rgb_image)
    print("MediaPipe image created")
except Exception as e:
    print(f"ERROR: Failed to create mp.Image: {type(e).__name__}: {e}")
    sys.exit(1)

# ── Run detection ──────────────────────────────────────────────────────────────
try:
    result = detector.detect(mp_image)
    print(f"Detection result: {result}")
    faces = result.face_landmarks if result and result.face_landmarks else []
    print(f"Faces detected: {len(faces)}")
    if len(faces) == 0:
        print("NOTE: No face detected. Ensure a real human face is in front of the camera with good lighting.")
    else:
        print(f"  → First face has {len(faces[0])} landmarks")
except Exception as e:
    print(f"ERROR: Detection failed: {type(e).__name__}: {e}")
    sys.exit(1)
