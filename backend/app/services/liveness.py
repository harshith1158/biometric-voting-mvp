import numpy as np


def compute_ear(landmarks: np.ndarray) -> float:
    """
    Compute Eye Aspect Ratio (EAR) from 6 eye landmark points.

    EAR = (dist(p2, p6) + dist(p3, p5)) / (2 * dist(p1, p4))

    Where p1-p6 are the 6 eye landmark points in order around the eye.
    p1, p4 form the horizontal eye opening (palpebral fissure).
    p2, p3, p5, p6 form the vertical distances.

    Args:
        landmarks: (6, 2) numpy array of (x, y) coordinates

    Returns:
        float: EAR value (lower values indicate closed/closed eyes)
    """
    if landmarks.shape[0] < 6 or landmarks.shape[1] != 2:
        return 1.0

    p1 = landmarks[0]
    p2 = landmarks[1]
    p3 = landmarks[2]
    p4 = landmarks[3]
    p5 = landmarks[4]
    p6 = landmarks[5]

    vert1 = np.linalg.norm(p2 - p6)
    vert2 = np.linalg.norm(p3 - p5)
    horiz = np.linalg.norm(p1 - p4)

    if horiz == 0:
        return 1.0

    ear = (vert1 + vert2) / (2.0 * horiz)
    return float(ear)


def detect_blink(
    left_eye: np.ndarray, right_eye: np.ndarray, threshold: float = 0.25
) -> tuple[bool, float]:
    """
    Detect eye closure (blink) using EAR from both eyes.

    If average EAR < threshold, eyes are considered closed (blink detected).

    Args:
        left_eye: (6, 2) numpy array of left eye landmark coordinates
        right_eye: (6, 2) numpy array of right eye landmark coordinates
        threshold: EAR threshold below which eye is considered closed (default 0.25)

    Returns:
        tuple: (blink_detected, ear_score)
            - blink_detected: bool, True if avg EAR < threshold
            - ear_score: float, average EAR across both eyes (rounded to 3 decimals)
    """
    try:
        left_ear = compute_ear(left_eye)
        right_ear = compute_ear(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0
        blink_detected = avg_ear < threshold
        return blink_detected, round(avg_ear, 3)
    except Exception:
        return False, 1.0
