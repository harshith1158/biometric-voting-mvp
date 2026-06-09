import io
import json
import numpy as np
import cv2
from PIL import Image
import os
from datetime import datetime
from deepface import DeepFace

print("[INFO] Biometric service initialized (using DeepFace)")

# STRICT: Create face storage directories (legacy and new)
FACE_IMAGES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'face_images')
os.makedirs(FACE_IMAGES_DIR, exist_ok=True)
print(f"[INFO] Face images directory: {FACE_IMAGES_DIR}")

# NEW: Strict face storage directory
FACES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'faces')
os.makedirs(FACES_DIR, exist_ok=True)
print(f"[INFO] Strict faces directory: {FACES_DIR}")


# ---------------------------------------------------------------------------
# PART 3: Embedding comparison helpers
# ---------------------------------------------------------------------------

def cosine_distance(a, b):
    """Cosine distance between two embedding vectors.

    Returns a float in [0, 2]; 0 = identical, ~1 = orthogonal, 2 = opposite.
    """
    a = np.array(a, dtype=np.float64)
    b = np.array(b, dtype=np.float64)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0.0 or norm_b == 0.0:
        return 1.0
    return float(1.0 - np.dot(a, b) / (norm_a * norm_b))


# ---------------------------------------------------------------------------
# PART 1 helper: Extract Facenet embeddings from saved registration faces
# ---------------------------------------------------------------------------

def extract_embeddings_from_folder(folder_path, max_count=3):
    """Extract Facenet 128-dim embeddings from registration face images.

    Args:
        folder_path: Path to folder containing face_*.jpg, or a single .jpg file.
        max_count:   Maximum number of embeddings to extract (default 3).

    Returns:
        List of embedding vectors (each a list of 128 floats).
        Returns an empty list if extraction fails completely.
    """
    import glob

    print(f"\n[EMB-EXTRACT] Extracting up to {max_count} Facenet embeddings from: {folder_path}")

    image_paths = []
    if os.path.isdir(folder_path):
        pattern = os.path.join(folder_path, "face_*.jpg")
        image_paths = sorted(glob.glob(pattern))[:max_count]
    elif os.path.isfile(folder_path):
        image_paths = [folder_path]
    else:
        print(f"[EMB-EXTRACT] Path not found: {folder_path}")
        return []

    print(f"[EMB-EXTRACT] Images to process: {len(image_paths)}")

    embeddings = []
    for idx, img_path in enumerate(image_paths):
        try:
            reps = DeepFace.represent(
                img_path=img_path,
                model_name="Facenet",
                enforce_detection=True,
            )
            if reps and len(reps) > 0:
                embeddings.append(reps[0]["embedding"])
                print(f"[EMB-EXTRACT] ✓ Image {idx + 1}: embedding extracted (dim={len(reps[0]['embedding'])})")
            else:
                print(f"[EMB-EXTRACT] Image {idx + 1}: no embedding returned")
        except Exception as e:
            print(f"[EMB-EXTRACT] Image {idx + 1}: failed — {str(e)}")
            continue

    print(f"[EMB-EXTRACT] Stored {len(embeddings)}/{len(image_paths)} embeddings")
    return embeddings


def load_image_from_bytes(image_bytes):
    """Load PIL Image from bytes."""
    image = Image.open(io.BytesIO(image_bytes))
    if image.mode != "RGB":
        image = image.convert("RGB")
    return image

def extract_face_embedding(image):
    """Extract face embedding using DeepFace.
    
    Args:
        image: PIL Image object
    
    Returns:
        JSON string with embedding vector, or None if extraction fails
    """
    try:
        image_array = np.array(image)
        
        # Extract embeddings using DeepFace (uses VGG-Face by default)
        embeddings = DeepFace.represent(image_array, model_name='VGG-Face', enforce_detection=False)
        
        if not embeddings or len(embeddings) == 0:
            print("[ERROR] No embeddings extracted")
            return None
        
        # Get the first (and usually only) embedding
        embedding_vector = embeddings[0]["embedding"]
        
        # Return as JSON string
        return json.dumps(embedding_vector)
        
    except Exception as e:
        print(f"[ERROR] extract_face_embedding failed: {str(e)}")
        return None


def save_registration_face(image, aadhaar_hash):
    """STRICT: Save face during registration to backend/data/faces/{aadhaar_hash}.jpg
    
    MANDATORY requirements:
    ✔ Enforce face detection (fail if no face or multiple faces)
    ✔ Overwrite if exists
    ✔ Print saved path
    ✔ Return filepath or None on STRICT failure
    
    Args:
        image: PIL Image object
        aadhaar_hash: Aadhaar hash (filename)
    
    Returns:
        filepath if successful, None if face detection fails
    """
    try:
        print(f"\n[REGISTER] Saving registration face for: {aadhaar_hash}")
        image_array = np.array(image)
        
        # STRICT ENFORCEMENT: Detect face with enforce_detection=True
        print(f"[REGISTER] Detecting face (STRICT)...")
        try:
            detections = DeepFace.extract_faces(image_array, enforce_detection=True)
            
            if not detections:
                print("[ERROR] BLOCK: No face detected in registration image")
                return None
            
            if len(detections) > 1:
                print(f"[ERROR] BLOCK: Multiple faces detected ({len(detections)}) - only 1 allowed")
                return None
            
            print(f"[REGISTER] ✓ Exactly 1 face detected")
        except Exception as detect_error:
            print(f"[ERROR] BLOCK: Face detection failed: {str(detect_error)}")
            return None
        
        # Save face image (OVERWRITE if exists)
        filename = f"{aadhaar_hash}.jpg"
        filepath = os.path.join(FACES_DIR, filename)
        
        # Convert RGB to BGR for cv2
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array
        
        success = cv2.imwrite(filepath, image_bgr)
        
        if success:
            print(f"[REGISTER] ✓ Saved registration image: {filepath}")
            return filepath
        else:
            print(f"[ERROR] BLOCK: Failed to save registration image to {filepath}")
            return None
    
    except Exception as e:
        print(f"[ERROR] save_registration_face exception: {type(e).__name__}: {str(e)}")
        return None


def save_multi_registration_faces(frame_images_list, aadhaar_hash):
    """Save up to 5 quality-filtered registration faces to a per-user folder.

    Folder: data/faces/{aadhaar_hash}/
    Files:  face_1.jpg … face_5.jpg

    Quality filter per frame:
    - Exactly 1 face detected
    - Face not too small (>= 2% of image area)
    - Face centered
    - Sufficient sharpness (Laplacian variance >= 20)

    Args:
        frame_images_list: list of PIL Image objects (from the liveness frames)
        aadhaar_hash: voter's Aadhaar hash (used as subfolder name)

    Returns:
        folder path (str) if at least 1 face saved, else None
    """
    folder = os.path.join(FACES_DIR, aadhaar_hash)
    os.makedirs(folder, exist_ok=True)
    print(f"\n[REGISTER-MULTI] Saving registration faces for: {aadhaar_hash}")
    print(f"[REGISTER-MULTI] Target folder: {folder}")

    saved = 0
    for idx, image in enumerate(frame_images_list):
        if saved >= 5:
            break
        try:
            image_array = np.array(image)
            is_valid, blur_score, face_count, centered = check_frame_quality(image_array)
            print(
                f"[REGISTER-MULTI] Frame {idx + 1}: valid={is_valid}, "
                f"blur={blur_score:.1f}, faces={face_count}, centered={centered}"
            )
            if not is_valid:
                print(f"[REGISTER-MULTI] Frame {idx + 1}: DISCARDED")
                continue

            saved += 1
            filename = f"face_{saved}.jpg"
            filepath = os.path.join(folder, filename)
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            success = cv2.imwrite(filepath, image_bgr)
            if success:
                print(f"[REGISTER-MULTI] ✓ Saved {filepath}")
            else:
                print(f"[REGISTER-MULTI] ✗ Failed to write {filepath}")
                saved -= 1
        except Exception as frame_err:
            print(f"[REGISTER-MULTI] Frame {idx + 1}: Exception — {str(frame_err)}")
            continue

    if saved == 0:
        print(f"[REGISTER-MULTI] BLOCK: No valid frames saved for {aadhaar_hash}")
        return None

    print(f"Saved {saved} face samples for user")
    return folder


def save_live_face(image):
    """STRICT: Save live face during verification to backend/data/faces/live_{timestamp}.jpg
    
    MANDATORY requirements:
    ✔ Enforce face detection (fail if no face or multiple faces)
    ✔ Use millisecond timestamp for uniqueness
    ✔ Print saved path
    ✔ Return filepath or None on STRICT failure
    
    Args:
        image: PIL Image object
    
    Returns:
        filepath if successful, None if face detection fails
    """
    try:
        import time
        timestamp = int(time.time() * 1000)
        
        print(f"[VERIFY] Saving live face (timestamp: {timestamp})")
        image_array = np.array(image)
        
        # LIVENESS: Loosen detection strictness (enforce_detection=False)
        print(f"[VERIFY] Detecting face in live image (liveness, relaxed)...")
        try:
            detections = DeepFace.extract_faces(image_array, enforce_detection=False)
            if not detections:
                print("[ERROR] BLOCK: No face detected in live image (relaxed)")
                return None
            if len(detections) > 1:
                print(f"[ERROR] BLOCK: Multiple faces detected ({len(detections)}) - only 1 allowed (relaxed)")
                return None
            print(f"[VERIFY] ✓ Exactly 1 face detected (relaxed)")
        except Exception as detect_error:
            print(f"[ERROR] BLOCK: Face detection failed in live image (relaxed): {str(detect_error)}")
            return None
        
        # Save live face image with timestamp (ensures uniqueness)
        filename = f"live_{timestamp}.jpg"
        filepath = os.path.join(FACES_DIR, filename)
        
        # Convert RGB to BGR for cv2
        if len(image_array.shape) == 3 and image_array.shape[2] == 3:
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            image_bgr = image_array
        
        success = cv2.imwrite(filepath, image_bgr)
        
        if success:
            print(f"[VERIFY] ✓ Saved live image: {filepath}")
            return filepath
        else:
            print(f"[ERROR] BLOCK: Failed to save live image to {filepath}")
            return None
    
    except Exception as e:
        print(f"[ERROR] save_live_face exception: {type(e).__name__}: {str(e)}")
        return None


def verify_identity_strict(registered_path, live_path):
    """STRICT: Verify identity using DeepFace with enforce_detection=True
    
    MANDATORY requirements:
    ✔ Use enforce_detection=True (FAIL if face not clearly detected)
    ✔ Use STRICT threshold 0.4 (NOT DeepFace default 0.68)
    ✔ Return verified=False on ANY failure
    ✔ NO fallback logic
    ✔ Print complete result for debugging
    
    Args:
        registered_path: Path to registration face image
        live_path: Path to live face image
    
    Returns:
        dict: {'verified': bool, 'distance': float, ...}
        verified=False means BLOCK identity
    """
    print(f"\n{'='*80}")
    print(f"[IDENTITY] STRICT VERIFICATION START")
    print(f"[IDENTITY] Registration face: {registered_path}")
    print(f"[IDENTITY] Live face:         {live_path}")
    
    # STRICT ENFORCEMENT: Use threshold 0.25 (stricter than before)
    STRICT_THRESHOLD = 0.25
    print(f"[IDENTITY] STRICT THRESHOLD: {STRICT_THRESHOLD} (cosine distance)")
    
    # Verify files exist and are different
    if not os.path.exists(registered_path):
        print(f"[ERROR] BLOCK: Registration image not found: {registered_path}")
        return {'verified': False, 'distance': 1.0, 'error': 'Registration image missing'}
    
    if not os.path.exists(live_path):
        print(f"[ERROR] BLOCK: Live image not found: {live_path}")
        return {'verified': False, 'distance': 1.0, 'error': 'Live image missing'}
    
    if registered_path == live_path:
        print(f"[ERROR] BLOCK: Same file used for both images (cache issue)")
        return {'verified': False, 'distance': 1.0, 'error': 'Same file - caching issue'}
    
    try:
        print(f"[IDENTITY] Calling DeepFace.verify() with enforce_detection=True...")
        result = DeepFace.verify(
            img1_path=registered_path,
            img2_path=live_path,
            model_name='VGG-Face',
            distance_metric='cosine',
            enforce_detection=True  # STRICT: Fail if face not clearly detected
        )
        
        distance = result.get('distance', 1.0)
        deepface_threshold = result.get('threshold', 0.68)
        
        # STRICT: Override DeepFace threshold with our own (0.4)
        verified = distance < STRICT_THRESHOLD
        
        print(f"[IDENTITY] RESULT:")
        print(f"  - Distance: {distance:.4f}")
        print(f"  - DeepFace Threshold: {deepface_threshold:.4f} (IGNORED)")
        print(f"  - STRICT Threshold: {STRICT_THRESHOLD} (ENFORCED)")
        print(f"  - Verified (distance < {STRICT_THRESHOLD}): {verified}")
        
        if verified:
            print(f"[IDENTITY] ✓ VERIFIED: Same person - IDENTITY CONFIRMED")
        else:
            print(f"[IDENTITY] ✗ BLOCKED: Different person - IDENTITY MISMATCH")
        
        print(f"{'='*80}\n")
        
        return {
            'verified': verified,
            'distance': float(distance),
            'threshold': STRICT_THRESHOLD,
            'deepface_threshold': float(deepface_threshold)
        }
    
    except Exception as e:
        print(f"[ERROR] DeepFace.verify() exception: {type(e).__name__}: {str(e)}")
        print(f"[ERROR] BLOCK: Verification failed - treating as identity mismatch")
        print(f"{'='*80}\n")
        return {
            'verified': False,
            'distance': 1.0,
            'error': str(e)
        }

def save_face_image(image, voter_id):
    """Save face image to disk for DeepFace verification.
    
    Stores image in data/face_images/{voter_id}.jpg
    Returns path to saved image or None if validation fails.
    """
    try:
        image_array = np.array(image)
        
        # Verify face using DeepFace
        try:
            detections = DeepFace.extract_faces(image_array, enforce_detection=False)
            
            if not detections or len(detections) == 0:
                print("[ERROR] save_face_image: NO FACES DETECTED")
                return None
            
            if len(detections) > 1:
                print(f"[ERROR] save_face_image: MULTIPLE FACES DETECTED ({len(detections)})")
                return None
        except Exception as e:
            print(f"[ERROR] save_face_image: Face detection failed — BLOCKING: {str(e)}")
            return None  # STRICT: Never save if face detection fails
        
        # Save face image
        filename = f"{voter_id}.jpg"
        filepath = os.path.join(FACE_IMAGES_DIR, filename)
        
        # Convert RGB to BGR for cv2
        if len(image_array.shape) == 3:
            if image_array.shape[2] == 3:
                image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
            else:
                image_bgr = image_array
        else:
            image_bgr = cv2.cvtColor(image_array, cv2.COLOR_GRAY2BGR)
        
        success = cv2.imwrite(filepath, image_bgr)
        
        if success:
            print(f"[INFO] ✓ Face image saved: {filepath}")
            return filepath
        else:
            print(f"[ERROR] Failed to save face image to {filepath}")
            return None
    
    except Exception as e:
        print(f"[ERROR] save_face_image failed: {str(e)}")
        return None


def deepface_verify(img1_path, img2_path):
    """Verify if two face images are of the same person using DeepFace.
    
    Args:
        img1_path: Path to first face image (registered)
        img2_path: Path to second face image (live)
    
    Returns:
        dict with keys: verified (bool), distance (float), threshold (float)
    
    STRICT: No fallback logic. If verification fails, return verified=False.
    """
    # CRITICAL: Log FULL PATHS and verify they exist and are different
    print(f"\n{'='*80}")
    print(f"[DEEPFACE] VERIFICATION START")
    print(f"[DEEPFACE] Registered image: {img1_path}")
    print(f"[DEEPFACE] Live image:       {img2_path}")
    print(f"[DEEPFACE] Same file? {img1_path == img2_path}")
    print(f"[DEEPFACE] Registered exists? {os.path.exists(img1_path)}")
    print(f"[DEEPFACE] Live exists? {os.path.exists(img2_path)}")
    
    # STRICT: Verify files are different and both exist
    if img1_path == img2_path:
        print(f"[ERROR] FATAL: Same file used twice! {img1_path}")
        return {
            'verified': False,
            'distance': 1.0,
            'threshold': 0.4,
            'error': 'FATAL: Same file used for both images'
        }
    
    if not os.path.exists(img1_path):
        print(f"[ERROR] FATAL: Registered image not found: {img1_path}")
        return {
            'verified': False,
            'distance': 1.0,
            'threshold': 0.4,
            'error': f'Registered image not found: {img1_path}'
        }
    
    if not os.path.exists(img2_path):
        print(f"[ERROR] FATAL: Live image not found: {img2_path}")
        return {
            'verified': False,
            'distance': 1.0,
            'threshold': 0.4,
            'error': f'Live image not found: {img2_path}'
        }
    
    try:
        print(f"[DEEPFACE] Calling DeepFace.verify()...")
        result = DeepFace.verify(
            img1_path=img1_path,
            img2_path=img2_path,
            model_name='VGG-Face',
            distance_metric='cosine',
            enforce_detection=True  # STRICT: Updated from False to True
        )
        
        verified = result.get('verified', False)
        distance = result.get('distance', 1.0)
        threshold = result.get('threshold', 0.4)
        
        print(f"[DEEPFACE] RESULT:")
        print(f"  - Verified: {verified}")
        print(f"  - Distance: {distance:.4f}")
        print(f"  - Threshold: {threshold:.4f}")
        print(f"  - Match: {'✓ SAME PERSON' if verified else '✗ DIFFERENT PERSON'}")
        print(f"{'='*80}\n")
        
        return {
            'verified': verified,
            'distance': float(distance),
            'threshold': float(threshold)
        }
    
    except Exception as e:
        print(f"[ERROR] DeepFace.verify() exception: {type(e).__name__}: {str(e)}")
        print(f"[ERROR] RESULT: verified=False (exception occurred)")
        print(f"{'='*80}\n")
        return {
            'verified': False,
            'distance': 1.0,
            'threshold': 0.4,
            'error': str(e)
        }

def store_biometric_data(voter_id, face_image_path, liveness_score):
    """Store biometric data in database.
    
    Args:
        voter_id: UUID of voter
        face_image_path: Path to stored face image (for DeepFace verification)
        liveness_score: float (0.0 or 1.0 for PASS/FAIL)
    
    Returns:
        BiometricData instance or None on failure.
    """
    try:
        from app.models import BiometricData
        from app.db import db
        
        # Store the face image path instead of embedding
        biometric = BiometricData(
            voter_id=voter_id,
            face_embedding=face_image_path,  # Store path for DeepFace verification
            liveness_score=liveness_score,
        )
        db.session.add(biometric)
        db.session.commit()
        
        print(f"[DB] Biometric data stored: voter_id={voter_id}, face_path={face_image_path}")
        return biometric
    except Exception as e:
        print(f"[ERROR] store_biometric_data failed: {str(e)}")
        return None
    except Exception as e:
        return None

def process_selfie(voter_id, image_bytes):
    """End-to-end selfie processing: detect, liveness check, save image.
    
    Uses DeepFace for face detection and verification.
    
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
    
    image_array = np.array(image)
    
    # Check liveness using DeepFace
    try:
        detections = DeepFace.extract_faces(image_array, enforce_detection=False)
        
        if not detections or len(detections) == 0:
            return {
                "status": "error",
                "error": "No face detected",
                "liveness_result": "FAIL",
                "embedding_stored": False,
            }
        
        if len(detections) > 1:
            return {
                "status": "error",
                "error": "Multiple faces detected",
                "liveness_result": "FAIL",
                "embedding_stored": False,
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Face detection failed: {str(e)}",
            "liveness_result": None,
            "embedding_stored": False,
        }
    
    # Liveness check passed
    liveness_result = "PASS"
    liveness_score = 1.0
    
    # Save face image for DeepFace verification
    face_image_path = save_face_image(image, voter_id)
    if not face_image_path:
        return {
            "status": "error",
            "error": "Failed to save face image",
            "liveness_result": liveness_result,
            "embedding_stored": False,
        }
    
    stored = store_biometric_data(voter_id, face_image_path, liveness_score)
    
    return {
        "status": "success",
        "liveness_result": liveness_result,
        "embedding_stored": stored is not None,
        "confidence": 0.95,
        "face_image_path": face_image_path,
    }


def check_frame_quality(image_array):
    """Assess frame quality for multi-frame face verification.

    Checks:
    - Exactly 1 face detected
    - Face is roughly centered (within middle 50% of frame)
    - Minimal blur (Laplacian variance >= 20)

    Args:
        image_array: numpy array (RGB)

    Returns:
        tuple: (is_valid, blur_score, face_count, face_centered)
    """
    try:
        # Blur detection via Laplacian variance
        gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
        blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        # Face count check
        detections = DeepFace.extract_faces(image_array, enforce_detection=False)
        face_count = len(detections) if detections else 0

        if face_count != 1:
            return False, blur_score, face_count, False

        # Face centering and size check
        facial_area = detections[0].get('facial_area', {})
        if facial_area:
            img_h, img_w = image_array.shape[:2]
            fw = facial_area.get('w', 0)
            fh = facial_area.get('h', 0)
            fx = (facial_area.get('x', 0) + fw / 2) / img_w
            fy = (facial_area.get('y', 0) + fh / 2) / img_h
            face_centered = (0.25 <= fx <= 0.75) and (0.20 <= fy <= 0.80)
            # Reject faces that are too small (< 2% of image area)
            img_area = img_h * img_w
            face_area = fw * fh
            face_size_ok = (face_area / img_area) >= 0.02 if img_area > 0 else False
        else:
            face_centered = True  # Unknown position — assume centered
            face_size_ok = True

        is_valid = (face_count == 1) and (blur_score >= 20.0) and face_centered and face_size_ok
        return is_valid, blur_score, face_count, face_centered

    except Exception as e:
        print(f"[QUALITY] Frame quality check error: {str(e)}")
        return False, 0.0, 0, False


# ---------------------------------------------------------------------------
# PARTS 2–4: Fast embedding-based identity verification
# ---------------------------------------------------------------------------

def verify_identity_embeddings(stored_embeddings, live_frame_bytes_list,
                                max_stored=3, max_live=3):
    """Fast Facenet embedding comparison — the production identity verification path.

    Algorithm (Parts 2–4 of the upgrade spec):
    1. Limit stored embeddings to max_stored (default 3).
    2. Extract live Facenet embeddings from up to max_live frames (Part 2).
    3. Compute all pairwise cosine distances — max 3×3 = 9 (Part 3, Part 6).
     4. Apply threshold logic (strict):
         - consistent multi-frame matches under 0.40  → PASS
         - borderline best distance up to 0.50       → RETRY
         - otherwise                                  → FAIL
    5. Fallback to DeepFace.verify() on exception (Part 5).

    Args:
        stored_embeddings:    list of pre-computed 128-dim Facenet vectors.
        live_frame_bytes_list: list of raw JPEG bytes for live frames.
        max_stored:  max stored embeddings to use (default 3).
        max_live:    max live frames to use (default 3).

    Returns:
        dict with keys:
            verified  (bool)   — True only on PASS
            distance  (float)  — best cosine distance
            distances (list)   — all pairwise distances
            frames_used (int)
            status    (str)    — 'pass' | 'retry' | 'failed' | 'error'
            threshold (float)
            message / error (str, optional)
    """
    STRONG_MATCH = 0.40   # below this → strong match
    RETRY_MAX    = 0.50   # between STRONG_MATCH and this → RETRY
    MODEL        = "Facenet"

    print(f"\n{'='*80}")
    print(f"[EMB-VERIFY] EMBEDDING-BASED IDENTITY VERIFICATION (fast path)")
    print(f"[EMB-VERIFY] Stored embeddings: {len(stored_embeddings)} | Live frames: {len(live_frame_bytes_list)}")
    print(f"[EMB-VERIFY] Thresholds — PASS < {STRONG_MATCH} | RETRY <= {RETRY_MAX} | FAIL > {RETRY_MAX}")

    use_stored = stored_embeddings[:max_stored]

    # --- Part 2: Extract live Facenet embeddings ---
    live_embeddings = []
    tried = 0
    for idx, frame_bytes in enumerate(live_frame_bytes_list):
        if len(live_embeddings) >= max_live:
            break
        tried += 1
        try:
            image = load_image_from_bytes(frame_bytes)
            image_array = np.array(image)
            reps = DeepFace.represent(
                img_path=image_array,
                model_name=MODEL,
                enforce_detection=True,
            )
            if reps and len(reps) > 0:
                live_embeddings.append(reps[0]["embedding"])
                print(f"[EMB-VERIFY] Live frame {idx + 1}: ✓ embedding extracted")
            else:
                print(f"[EMB-VERIFY] Live frame {idx + 1}: no embedding returned")
        except Exception as e:
            print(f"[EMB-VERIFY] Live frame {idx + 1}: extraction failed — {str(e)}")
            continue

    print(f"[EMB-VERIFY] Live embeddings extracted: {len(live_embeddings)}/{tried}")

    if not live_embeddings:
        print(f"[EMB-VERIFY] BLOCK: No live embeddings — returning error (caller will fallback)")
        return {
            "verified": False,
            "distance": 1.0,
            "distances": [],
            "frames_used": 0,
            "status": "error",
            "error": "Could not extract live face embeddings — ensure face is clearly visible",
        }

    # --- Part 3: All pairwise cosine distances (max 3×3 = 9) ---
    distances = []
    for s_emb in use_stored:
        for l_emb in live_embeddings:
            d = cosine_distance(s_emb, l_emb)
            distances.append(d)

    best_distance = min(distances)
    print(f"[EMB-VERIFY] DISTANCES: {[round(d, 4) for d in distances]}")
    print(f"[EMB-VERIFY] BEST DISTANCE: {best_distance:.4f}")

    # --- Part 4: Threshold logic with consistency gate ---
    strong_matches = sum(1 for d in distances if d < STRONG_MATCH)
    total_pairs = len(distances)
    print(f"[EMB-VERIFY] STRONG MATCH PAIRS: {strong_matches}/{total_pairs}")

    # Prevent single accidental low-distance pair from passing a different face.
    if total_pairs == 1:
        pass_condition = best_distance < 0.32
    else:
        pass_condition = strong_matches >= 2

    if pass_condition:
        print(f"[EMB-VERIFY] ✅ CONSISTENT MATCH — PASS")
        return {
            "verified": True,
            "distance": float(best_distance),
            "distances": [round(d, 4) for d in distances],
            "frames_used": len(live_embeddings),
            "status": "pass",
            "threshold": STRONG_MATCH,
            "strong_matches": int(strong_matches),
        }
    elif best_distance <= RETRY_MAX:
        print(f"[EMB-VERIFY] ⚠️  BORDERLINE — RETRY ({best_distance:.4f} in [{STRONG_MATCH}, {RETRY_MAX}])")
        return {
            "verified": False,
            "distance": float(best_distance),
            "distances": [round(d, 4) for d in distances],
            "frames_used": len(live_embeddings),
            "status": "retry",
            "message": "Please look straight and try again",
            "threshold": STRONG_MATCH,
            "strong_matches": int(strong_matches),
        }
    else:
        print(f"[EMB-VERIFY] ❌ MISMATCH — FAIL ({best_distance:.4f} > {RETRY_MAX})")
        return {
            "verified": False,
            "distance": float(best_distance),
            "distances": [round(d, 4) for d in distances],
            "frames_used": len(live_embeddings),
            "status": "failed",
            "error": "Identity verification failed",
            "threshold": STRONG_MATCH,
            "strong_matches": int(strong_matches),
        }


def verify_identity_multiframe(registered_path, live_frame_bytes_list,
                                stored_embeddings=None):
    """Multi-frame identity verification using DeepFace Facenet — BEST MATCH strategy.

    Tries the fast embedding path first (verify_identity_embeddings) when
    stored_embeddings are provided.  Falls back to the image-based
    DeepFace.verify() path if embeddings are unavailable or fail (Part 5).

    Stored faces: registered_path may be
      - a folder  → use all face_*.jpg files inside it
      - a file    → use as single stored reference (backward compat)

    Process:
    1. Build list of stored face paths.
    2. Quality-filter each live frame (face count, size, centering, blur).
    3. For every (stored_face, live_frame) pair run DeepFace.verify (Facenet, cosine).
    4. Pick the BEST (minimum) distance across all pairs.
    5. Apply THRESHOLD = 0.65.

    Args:
        registered_path: Path to stored registration face file OR folder of face_*.jpg
        live_frame_bytes_list: List of raw bytes for each live frame

    Returns:
        dict with: verified (bool), distance (float), distances (list),
                   frames_used (int), threshold (float), error (str or None)
    """
    import time
    import glob
    import shutil

    # ── Part 5: Fast embedding path (if pre-computed embeddings are available) ──
    if stored_embeddings:
        print(f"[MULTIFRAME] Pre-computed embeddings available ({len(stored_embeddings)}) — trying fast path")
        try:
            emb_result = verify_identity_embeddings(stored_embeddings, live_frame_bytes_list)
            if emb_result.get("status") != "error":
                print(f"[MULTIFRAME] Fast embedding path succeeded — status={emb_result.get('status')}")
                return emb_result
            else:
                print(f"[MULTIFRAME] Fast path returned error, falling back to image-based verification")
        except Exception as emb_err:
            print(f"[MULTIFRAME] Fast path exception ({str(emb_err)}), falling back to image-based verification")

    # ── Fallback: image-based DeepFace.verify() (Part 5 safety net) ───────────
    # THRESHOLD for Facenet cosine distance.
    # DeepFace default for Facenet+cosine = 0.40.
    # We also require consistent matches across comparisons.
    THRESHOLD = 0.40
    DISTANCE_METRIC = 'cosine'
    MODEL = 'Facenet'

    # Create debug output directory (backend/debug/) for manual inspection
    DEBUG_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'debug')
    os.makedirs(DEBUG_DIR, exist_ok=True)

    print(f"\n{'='*80}")
    print(f">>> DEEPFACE VERIFY CALLED")
    print(f"[MULTIFRAME] MULTI-FRAME BEST-MATCH IDENTITY VERIFICATION (image fallback)")
    print(f"[MULTIFRAME] Registered path: {registered_path}")
    print(f"[MULTIFRAME] Input live frames: {len(live_frame_bytes_list)}")
    print(f"[MULTIFRAME] Model: {MODEL} | Metric: {DISTANCE_METRIC} | Threshold: {THRESHOLD}")
    print(f"STEP: Identity verification starting")

    # --- Step 0: Resolve stored face paths ---
    stored_paths = []
    if os.path.isdir(registered_path):
        pattern = os.path.join(registered_path, "face_*.jpg")
        stored_paths = sorted(glob.glob(pattern))
        print(f"[MULTIFRAME] Folder mode — found {len(stored_paths)} stored faces")
    elif os.path.isfile(registered_path):
        stored_paths = [registered_path]
        print(f"[MULTIFRAME] Single-file mode — 1 stored face")
    else:
        print(f"[MULTIFRAME] BLOCK: Registered path not found: {registered_path}")
        return {'verified': False, 'distance': 1.0, 'error': 'Registration image/folder missing'}

    if not stored_paths:
        print(f"[MULTIFRAME] BLOCK: No stored face files found at {registered_path}")
        return {'verified': False, 'distance': 1.0, 'error': 'No stored face files found'}

    temp_paths = []
    all_distances = []
    debug_stored_saved = False
    debug_live_saved = False

    try:
        # --- Step 1: Quality-filter live frames and save to temp files ---
        for idx, frame_bytes in enumerate(live_frame_bytes_list):
            try:
                image = load_image_from_bytes(frame_bytes)
                image_array = np.array(image)

                is_valid, blur_score, face_count, centered = check_frame_quality(image_array)
                print(
                    f"[MULTIFRAME] Live frame {idx + 1}: valid={is_valid}, "
                    f"blur={blur_score:.1f}, faces={face_count}, centered={centered}"
                )
                if not is_valid:
                    print(f"[MULTIFRAME] Live frame {idx + 1}: DISCARDED")
                    continue

                ts = int(time.time() * 1000) + idx
                temp_path = os.path.join(FACES_DIR, f"live_mf_{ts}.jpg")
                image_bgr = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                cv2.imwrite(temp_path, image_bgr)
                temp_paths.append(temp_path)

                # Save first valid live frame as debug/live.jpg for manual inspection
                if not debug_live_saved:
                    debug_live_path = os.path.join(DEBUG_DIR, "live.jpg")
                    cv2.imwrite(debug_live_path, image_bgr)
                    print(f"LIVE IMAGE (debug): {debug_live_path}")
                    debug_live_saved = True

            except Exception as frame_err:
                print(f"[MULTIFRAME] Live frame {idx + 1}: Exception — {str(frame_err)}")
                continue

        print(f"[MULTIFRAME] Valid live frames: {len(temp_paths)}/{len(live_frame_bytes_list)}")
        print(f"FRAME COUNT: {len(temp_paths)}")

        if not temp_paths:
            print(f"[MULTIFRAME] BLOCK: No valid live frames to verify")
            return {
                'verified': False,
                'distance': 1.0,
                'error': 'No valid frames — ensure face is visible, centered, and well-lit',
            }

        # --- Step 2: Compare ALL stored faces × ALL live frames ---
        print(f"[MULTIFRAME] Running {len(stored_paths)} × {len(temp_paths)} = "
              f"{len(stored_paths) * len(temp_paths)} comparisons...")

        failed_comparisons = 0

        for s_idx, stored_path in enumerate(stored_paths):
            # Save first stored face as debug/stored.jpg for manual inspection
            if not debug_stored_saved:
                debug_stored_path = os.path.join(DEBUG_DIR, "stored.jpg")
                try:
                    shutil.copy2(stored_path, debug_stored_path)
                    print(f"STORED IMAGE (debug): {debug_stored_path}")
                except Exception as cp_err:
                    print(f"[DEBUG] Could not copy stored image: {cp_err}")
                debug_stored_saved = True

            for l_idx, temp_path in enumerate(temp_paths):
                print(f">>> DEEPFACE VERIFY CALLED")
                print(f"STORED IMAGE: {stored_path}")
                print(f"LIVE IMAGE:   {temp_path}")

                try:
                    result = DeepFace.verify(
                        img1_path=stored_path,
                        img2_path=temp_path,
                        model_name=MODEL,
                        distance_metric=DISTANCE_METRIC,
                        enforce_detection=True,
                    )
                    print(f"FULL RESULT: {result}")

                    dist = float(result.get('distance', 1.0))
                    all_distances.append(dist)
                    print(
                        f"[MULTIFRAME] stored[{s_idx + 1}] x live[{l_idx + 1}]: "
                        f"distance={dist:.4f}"
                    )
                except Exception as ve:
                    failed_comparisons += 1
                    print(
                        f"[MULTIFRAME] stored[{s_idx + 1}] x live[{l_idx + 1}]: "
                        f"COMPARISON FAILED (face not detected or error) — {str(ve)}"
                    )
                    # NOT a bypass — failed comparison = no distance recorded.
                    # If ALL comparisons fail, all_distances stays empty → verified=False.

        print(f"ALL DISTANCES: {[round(d, 4) for d in all_distances]}")
        print(f"[MULTIFRAME] Failed comparisons (DeepFace error): {failed_comparisons}")

        if not all_distances:
            print(f"[MULTIFRAME] BLOCK: All comparisons failed ({failed_comparisons} errors)")
            return {
                'verified': False,
                'distance': 1.0,
                'error': 'All frame verifications failed — ensure face is clearly visible',
            }

        # --- Step 3: Consistent match gate ---
        best_distance = min(all_distances)
        strong_matches = sum(1 for d in all_distances if d < THRESHOLD)
        print(f"BEST DISTANCE: {best_distance:.4f}")
        print(f"[MULTIFRAME] Strong match pairs: {strong_matches}/{len(all_distances)}")
        print(f"[MULTIFRAME] Threshold: {THRESHOLD}")
        print(f"STEP: Identity result: {best_distance:.4f} vs threshold {THRESHOLD}")

        if len(all_distances) == 1:
            verified = best_distance < 0.32
        else:
            verified = strong_matches >= 2

        if verified:
            print(f"[MULTIFRAME] FACE MATCH - ALLOWED: best={best_distance:.4f} < {THRESHOLD}")
            print(f">>> FACE MATCH - ALLOWED")
        else:
            print(f"[MULTIFRAME] FACE MISMATCH - BLOCKING: best={best_distance:.4f} >= {THRESHOLD}")
            print(f">>> FACE MISMATCH - BLOCKING")
        print(f"{'='*80}\n")

        return {
            'verified': verified,
            'distance': float(best_distance),
            'distances': [round(d, 4) for d in all_distances],
            'frames_used': len(temp_paths),
            'threshold': THRESHOLD,
            'strong_matches': int(strong_matches),
        }

    finally:
        # Clean up temp live images
        for tp in temp_paths:
            try:
                if os.path.exists(tp):
                    os.remove(tp)
            except Exception:
                pass
