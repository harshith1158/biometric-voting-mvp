import cv2


def extract_features(image_path):
    img = cv2.imread(image_path, 0)
    if img is None:
        return None

    orb = cv2.ORB_create()
    _, descriptors = orb.detectAndCompute(img, None)
    return descriptors


def match_score(desc1, desc2):
    if desc1 is None or desc2 is None:
        return 0

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    matches = bf.match(desc1, desc2)

    return len(matches)
