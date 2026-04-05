"""
Extract facial landmarks using MediaPipe FaceLandmarker (Tasks API).
Uses the pre-trained face_landmarker.task model.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Cache detector at module level to avoid reloading
_detector = None

# ── Startup model path verification ──────────────────────────────────────────
_model_path = Path(__file__).resolve().parents[1] / 'models' / 'face_landmarker.task'
print(f"MODEL PATH: {_model_path}")
print(f"MODEL EXISTS: {_model_path.exists()}")
if not _model_path.exists():
    print("ERROR: face_landmarker.task not found — face detection will fail on first request")
# ─────────────────────────────────────────────────────────────────────────────

def _get_detector():
    """Lazy-load and cache the MediaPipe FaceLandmarker model."""
    global _detector
    if _detector is None:
        try:
            from mediapipe.tasks import python
            from mediapipe.tasks.python import vision
            
            model_path = Path(__file__).resolve().parents[1] / 'models' / 'face_landmarker.task'
            
            if not model_path.exists():
                raise FileNotFoundError(f"Model not found: {model_path}")
            
            base_options = python.BaseOptions(model_asset_path=str(model_path))
            options = vision.FaceLandmarkerOptions(
                base_options=base_options,
                output_face_blendshapes=False
            )
            _detector = vision.FaceLandmarker.create_from_options(options)
            logger.info(f"[✓] MediaPipe FaceLandmarker model loaded from {model_path}")
        except Exception as e:
            logger.error(f"[✗] Failed to load MediaPipe model: {str(e)}")
            raise RuntimeError(f"MediaPipe model loading failed: {str(e)}")
    
    return _detector


def extract_eye_landmarks(bgr_image):
    """
    Extract eye landmarks from an image using MediaPipe FaceLandmarker.
    
    Args:
        bgr_image: BGR image as numpy array (OpenCV format)
    
    Returns:
        tuple: (left_eye_landmarks, right_eye_landmarks, all_landmarks)
            - left_eye_landmarks: (6, 2) numpy array for left eye
            - right_eye_landmarks: (6, 2) numpy array for right eye
            - all_landmarks: list of all 468 face landmarks as [x, y] pairs
    
    Raises:
        ValueError: If image is invalid
        RuntimeError: If face detection fails
    """
    import numpy as np

    # Validate input
    if bgr_image is None:
        raise ValueError("Invalid image input: None provided")
    
    if not isinstance(bgr_image, np.ndarray):
        raise ValueError(f"Invalid image type: expected numpy array, got {type(bgr_image)}")
    
    if bgr_image.size == 0:
        raise ValueError("Invalid image: empty array")
    
    h, w = bgr_image.shape[:2]
    
    if h < 100 or w < 100:
        logger.warning(f"Small image ({h}x{w}). Face detection may fail.")
    
    try:
        try:
            import cv2
        except Exception as e_cv2:
            raise RuntimeError(f"OpenCV unavailable: {str(e_cv2)}")

        # Convert BGR to RGB (MediaPipe expects RGB)
        rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
        logger.info(f"[IMAGE] BGR→RGB conversion done. Original shape: {bgr_image.shape}, RGB shape: {rgb_image.shape}, dtype: {rgb_image.dtype}, min/max: {rgb_image.min()}/{rgb_image.max()}")
        
        # Ensure array is contiguous and uint8
        rgb_image_uint8 = np.ascontiguousarray(rgb_image.astype(np.uint8))
        logger.info(f"[IMAGE] RGB uint8 prepared. Contiguous: {rgb_image_uint8.flags['C_CONTIGUOUS']}, shape: {rgb_image_uint8.shape}, nbytes: {rgb_image_uint8.nbytes}")
        
        # Get detector
        detector = _get_detector()
        logger.info(f"[DETECTOR] Loaded and ready")
        
        # Import Image class from correct location
        from mediapipe.tasks.python.vision.core.image import Image as mp_Image
        from mediapipe import ImageFormat
        
        # Test Image creation
        logger.info(f"[IMAGE] Creating MediaPipe Image with format={ImageFormat.SRGB}, data shape={rgb_image_uint8.shape}")
        try:
            mp_image = mp_Image(
                image_format=ImageFormat.SRGB,
                data=rgb_image_uint8
            )
            logger.info(f"[IMAGE] MediaPipe Image created successfully: {type(mp_image)}")
        except Exception as e_img:
            logger.error(f"[IMAGE] CRITICAL: Failed to create Image object: {type(e_img).__name__}: {str(e_img)}")
            raise RuntimeError(f"Image creation failed: {str(e_img)}")
        
        # Detect face landmarks
        logger.info(f"[DETECT] Starting detector.detect() call with {w}x{h} image, {rgb_image_uint8.nbytes} bytes...")
        try:
            detection_result = detector.detect(mp_image)
            logger.info(f"[DETECT] Detection completed successfully")
        except Exception as e_detect:
            logger.error(f"[DETECT] CRITICAL: Detection failed at detector.detect() call: {type(e_detect).__name__}: {str(e_detect)}")
            raise RuntimeError(f"Detection call failed: {str(e_detect)}")
        
        if not detection_result or not detection_result.face_landmarks or len(detection_result.face_landmarks) == 0:
            logger.warning(f"[DETECT] No faces detected in image (result={detection_result})")
            raise RuntimeError("No face detected in image")

        if len(detection_result.face_landmarks) != 1:
            logger.warning(f"[DETECT] Expected exactly 1 face, got {len(detection_result.face_landmarks)}")
            raise RuntimeError("Exactly one face required")

        # Get first detected face
        landmarks = detection_result.face_landmarks[0]
        logger.info(f"[DETECT] ✓ Face detected with {len(landmarks)} landmarks")
        
    except Exception as e:
        logger.error(f"[✗] extract_eye_landmarks FAILED at {type(e).__name__}: {str(e)}", exc_info=True)
        
        # Try to provide more specific error context
        if "Image" in str(type(e)):
            logger.error("[IMAGE ERROR] Problem creating MediaPipe Image object")
        elif "detect" in str(e).lower():
            logger.error("[DETECT ERROR] Problem during face detection call")
        elif "No face detected" in str(e):
            logger.warning("[NO FACE] No faces found in the image")
        
        raise RuntimeError(f"Face landmark extraction failed: {str(e)}")
    
    # Extract eye landmarks from 468-point face mesh
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
    
    # Convert all 468 landmarks to pixel coordinates
    all_landmarks_list = []
    for lm in landmarks:
        all_landmarks_list.append([lm.x * w, lm.y * h])
    
    logger.info(f"Face landmarks extracted: {len(all_landmarks_list)} points")
    
    return left_eye, right_eye, all_landmarks_list
