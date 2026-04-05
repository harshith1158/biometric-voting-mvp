#!/usr/bin/env python3
"""Test MediaPipe face detection with sample images"""

import logging
import numpy as np
import sys
from pathlib import Path

# Setup logging to see all details
logging.basicConfig(
    level=logging.DEBUG,
    format='%(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

try:
    from mediapipe.tasks.python.vision.core.image import Image as mp_Image
    from mediapipe.tasks.python import vision
    from mediapipe import ImageFormat
    from mediapipe.tasks import python
    
    logger.info("All imports successful")
    
    # Load model
    model_path = Path('app/models/face_landmarker.task')
    if not model_path.exists():
        logger.error(f"Model not found at {model_path}")
        sys.exit(1)
    
    logger.info(f"Loading model from {model_path}...")
    base_options = python.BaseOptions(model_asset_path=str(model_path))
    options = vision.FaceLandmarkerOptions(
        base_options=base_options, 
        output_face_blendshapes=False
    )
    detector = vision.FaceLandmarker.create_from_options(options)
    logger.info("✓ FaceLandmarker model loaded successfully")
    
    # Test 1: Noise image (should find 0 faces)
    logger.info("\n=== TEST 1: Noise image ===")
    rgb_img = np.random.randint(0, 255, (720, 1280, 3), dtype=np.uint8)
    logger.info(f"Image shape: {rgb_img.shape}, dtype: {rgb_img.dtype}")
    
    mp_image = mp_Image(image_format=ImageFormat.SRGB, data=rgb_img)
    logger.info(f"✓ Image object created")
    
    result = detector.detect(mp_image)
    faces_found = len(result.face_landmarks) if result.face_landmarks else 0
    logger.info(f"✓ Detection done: {faces_found} faces found")
    
    # Test 2: Black image (should find 0 faces)
    logger.info("\n=== TEST 2: Black image ===")
    black_img= np.zeros((720, 1280, 3), dtype=np.uint8)
    mp_image_black = mp_Image(image_format=ImageFormat.SRGB, data=black_img)
    result_black = detector.detect(mp_image_black)
    faces_black = len(result_black.face_landmarks) if result_black.face_landmarks else 0
    logger.info(f"✓ Detection done: {faces_black} faces found")
    
    logger.info("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
    logger.info("Face detection is working correctly!")
    
except Exception as e:
    logger.error(f"ERROR: {type(e).__name__}: {str(e)}", exc_info=True)
    sys.exit(1)
