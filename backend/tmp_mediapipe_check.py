import sys
try:
    import mediapipe as mp
    import numpy as np
    import cv2
except Exception as e:
    print('IMPORT_ERROR', type(e).__name__, e)
    sys.exit(2)
print('mp.__version__=', getattr(mp,'__version__',None))
print('has solutions:', hasattr(mp,'solutions'))
print('has face_mesh:', hasattr(mp.solutions,'face_mesh') if hasattr(mp,'solutions') else False)
try:
    fm = mp.solutions.face_mesh.FaceMesh(static_image_mode=True, max_num_faces=1, refine_landmarks=True)
    img = np.zeros((480,640,3), dtype=np.uint8)
    res = fm.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    print('process_ok, multi_face_landmarks:', bool(getattr(res,'multi_face_landmarks', None)))
    fm.close()
except Exception as e:
    print('FACEMESH_ERROR', type(e).__name__, e)
    sys.exit(3)
print('OK')
sys.exit(0)
