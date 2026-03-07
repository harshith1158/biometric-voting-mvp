import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

model_path = 'app/models/face_landmarker.task'
base_options = BaseOptions(model_asset_path=model_path)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=False,
    output_facial_transformation_matrixes=False,
    num_faces=1,
)
face_landmarker = vision.FaceLandmarker.create_from_options(options)

# create dummy image
img = np.zeros((480, 640, 3), dtype=np.uint8)
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)

res = face_landmarker.detect(mp_image)
print('result type:', type(res))
fl = getattr(res, 'face_landmarks', None)
print('face_landmarks attr:', type(fl))
if fl:
    print('face_landmarks len:', len(fl))
    print('first element type:', type(fl[0]))
    if len(fl) and len(fl[0]):
        print('first landmark element type:', type(fl[0][0]))
    else:
        print('no landmarks present in first face')
else:
    print('no face_landmarks')
