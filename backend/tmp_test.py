import numpy as np, cv2
from app.routes.biometrics import extract_eye_landmarks

# create fake landmarks list-of-lists structure
class FakeLandmark:
    def __init__(self, x, y):
        self.x = x
        self.y = y

# create mesh as list of FakeLandmark
mesh = [FakeLandmark(0.5,0.5) for _ in range(470)]
# wrap in a list to simulate face_landmarks from mediapipe
fake_result = type('R', (), {'face_landmarks': [mesh]})

# monkeypatch extract_eye_landmarks internals by bypassing media-pipe call
# we'll copy the logic after the detect() call:
def test_with_mesh(mesh):
    h, w = 480, 640
    left_idx = [33, 160, 158, 133, 153, 144]
    right_idx = [362, 385, 387, 263, 373, 380]
    # reuse helper code from biometrics
    # convert mesh entries to normal
    def to_xy(lm):
        if hasattr(lm, 'x') and hasattr(lm, 'y'):
            return int(lm.x * w), int(lm.y * h)
        if isinstance(lm, (list, tuple)) and len(lm) >= 2:
            return int(lm[0] * w), int(lm[1] * h)
        raise ValueError('unsupported')
    def coords(indices):
        pts=[]
        for i in indices:
            lm = mesh[i]
            x_px,y_px = to_xy(lm)
            pts.append([x_px,y_px])
        return np.array(pts, dtype=np.float32)
    return coords(left_idx), coords(right_idx), mesh

print('fake test: ', test_with_mesh(mesh))

# also simulate mesh being plain list (no object) -> list-of-lists
mesh2 = [[0.1,0.2] for _ in range(470)]
fake_result2 = type('R', (), {'face_landmarks': [mesh2]})

# ensure extract_eye_landmarks can handle via direct call
def simulate(result):
    # mimic part of extract_eye_landmarks
    faces = getattr(result, 'face_landmarks', None)
    if not faces:
        return None
    m = faces[0]
    if hasattr(m,'landmarks'):
        m = m.landmarks
    h,w,_ = 480,640,3
    left_idx=[33,160,158,133,153,144]
    right_idx=[362,385,387,263,373,380]
    def to_xy(lm):
        if hasattr(lm,'x') and hasattr(lm,'y'):
            return int(lm.x*w), int(lm.y*h)
        if isinstance(lm,(list,tuple)) and len(lm)>=2:
            return int(lm[0]*w), int(lm[1]*h)
        raise ValueError
    for i in left_idx:
        print('left',to_xy(m[i]))
    return True

print('simulate1', simulate(fake_result))
print('simulate2', simulate(fake_result2))
