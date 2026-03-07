import numpy as np, cv2, mediapipe as mp
from mediapipe.tasks.python import vision, BaseOptions

model_path = 'app/models/face_landmarker.task'
face_landmarker = vision.FaceLandmarker.create_from_options(
    vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        output_face_blendshapes=False,
        output_facial_transformation_matrixes=False,
        num_faces=1,
    )
)

# create dummy image
img = np.zeros((480,640,3), dtype=np.uint8)
mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img)
res = face_landmarker.detect(mp_image)
print('result type', type(res))
print(res)
print('dir result', dir(res))
if hasattr(res, 'face_landmarks'):
    print('face_landmarks attr', res.face_landmarks)
else:
    print('no face_landmarks attr')
    try:
        print('trying as iterable: len', len(res))
        print('element type', type(res[0]), res[0])
    except Exception as e:
        print('iteration error', e)
