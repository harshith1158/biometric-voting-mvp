import numpy as np
import logging

logger = logging.getLogger(__name__)


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
    if landmarks is None or landmarks.shape[0] < 6 or landmarks.shape[1] != 2:
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
    
    Raises:
        ValueError: If eye landmarks are invalid
    """
    try:
        if left_eye is None or right_eye is None:
            raise ValueError("Eye landmarks cannot be None")
        
        left_ear = compute_ear(left_eye)
        right_ear = compute_ear(right_eye)
        avg_ear = (left_ear + right_ear) / 2.0
        blink_detected = avg_ear < threshold
        return blink_detected, round(avg_ear, 3)
    except Exception as e:
        logger.error(f"Blink detection error: {str(e)}")
        raise RuntimeError(f"Blink detection failed: {str(e)}")


def detect_blink_sequence(
    ear_values: list[float],
    absolute_threshold: float = 0.25,
    min_drop: float = 0.020,
    reopen_margin: float = 0.015,
) -> tuple[bool, dict]:
    """
    Detect a blink from a sequence of EAR values using adaptive thresholds.

    This is more robust than a single absolute EAR cutoff because glasses,
    camera angle, and face shape can shift the baseline EAR substantially.

    A blink-like sequence is considered present when:
    - there is enough EAR variation across the sequence,
    - the EAR drops below a closed-eye threshold derived from the user's own
      baseline EAR, and
    - the sequence shows open -> closed -> open progression.

    min_drop is set to 0.020 (was 0.035) to handle glasses wearers whose
    compressed EAR range produces smaller absolute drops during a blink.
    """
    try:
        if not ear_values or len(ear_values) < 3:
            return False, {
                "reason": "insufficient_frames",
                "baseline": 0.0,
                "min_ear": 0.0,
                "max_ear": 0.0,
                "drop": 0.0,
            }

        values = np.array(ear_values, dtype=np.float32)
        # Use 75th percentile as baseline (was 80th).  For glasses wearers the
        # EAR distribution is compressed downward, so a lower percentile gives
        # a better estimate of the "eyes open" state.
        baseline = float(np.percentile(values, 75))
        min_ear = float(values.min())
        max_ear = float(values.max())
        ear_drop = max_ear - min_ear

        adaptive_closed_threshold = min(absolute_threshold, baseline - min_drop)
        # Floor lowered from 0.12 → 0.08 so glasses wearers with naturally
        # low EAR can still be detected as blinking.
        adaptive_closed_threshold = max(adaptive_closed_threshold, 0.08)
        open_threshold = max(baseline - reopen_margin, adaptive_closed_threshold + 0.01)

        if ear_drop < min_drop:
            return False, {
                "reason": "ear_variation_too_small",
                "baseline": round(baseline, 4),
                "min_ear": round(min_ear, 4),
                "max_ear": round(max_ear, 4),
                "drop": round(ear_drop, 4),
                "closed_threshold": round(adaptive_closed_threshold, 4),
                "open_threshold": round(open_threshold, 4),
            }

        closed_indices = [index for index, value in enumerate(values) if float(value) <= adaptive_closed_threshold]

        for closed_index in closed_indices:
            has_open_before = any(float(value) >= open_threshold for value in values[:closed_index])
            has_open_after = any(float(value) >= open_threshold for value in values[closed_index + 1:])

            if has_open_before and has_open_after:
                return True, {
                    "reason": "open_closed_open_sequence",
                    "baseline": round(baseline, 4),
                    "min_ear": round(min_ear, 4),
                    "max_ear": round(max_ear, 4),
                    "drop": round(ear_drop, 4),
                    "closed_threshold": round(adaptive_closed_threshold, 4),
                    "open_threshold": round(open_threshold, 4),
                    "closed_index": int(closed_index),
                }

        # Fallback: strong EAR drop even without post-blink reopen frames.
        # This handles the case where the blink happens near the end of the
        # capture window and we never record a post-blink open frame.
        # Require 3× min_drop (0.060) as the evidence bar is lower.
        STRONG_DROP = 3 * min_drop  # = 0.060
        if ear_drop >= STRONG_DROP and closed_indices:
            best_closed_idx = min(closed_indices, key=lambda i: float(values[i]))
            has_open_before = any(float(value) >= open_threshold for value in values[:best_closed_idx])
            if has_open_before:
                return True, {
                    "reason": "strong_drop_blink_fallback",
                    "baseline": round(baseline, 4),
                    "min_ear": round(min_ear, 4),
                    "max_ear": round(max_ear, 4),
                    "drop": round(ear_drop, 4),
                    "closed_threshold": round(adaptive_closed_threshold, 4),
                    "open_threshold": round(open_threshold, 4),
                    "closed_index": int(best_closed_idx),
                }

        # Quick blink fallback: 2+ consecutive frames below threshold.
        # Replaces the long blink duration requirement — catches fast natural
        # blinks without needing a post-blink open frame in the sequence.
        consecutive_closed = 0
        for v in values:
            if float(v) < adaptive_closed_threshold:
                consecutive_closed += 1
                if consecutive_closed >= 2:
                    return True, {
                        "reason": "quick_blink_consecutive_frames",
                        "baseline": round(baseline, 4),
                        "min_ear": round(min_ear, 4),
                        "max_ear": round(max_ear, 4),
                        "drop": round(ear_drop, 4),
                        "closed_threshold": round(adaptive_closed_threshold, 4),
                        "open_threshold": round(open_threshold, 4),
                        "consecutive_closed": consecutive_closed,
                    }
            else:
                consecutive_closed = 0

        return False, {
            "reason": "no_open_closed_open_sequence",
            "baseline": round(baseline, 4),
            "min_ear": round(min_ear, 4),
            "max_ear": round(max_ear, 4),
            "drop": round(ear_drop, 4),
            "closed_threshold": round(adaptive_closed_threshold, 4),
            "open_threshold": round(open_threshold, 4),
        }
    except Exception as error:
        logger.error(f"Blink sequence detection error: {str(error)}")
        return False, {
            "reason": f"exception: {str(error)}",
            "baseline": 0.0,
            "min_ear": 0.0,
            "max_ear": 0.0,
            "drop": 0.0,
        }
