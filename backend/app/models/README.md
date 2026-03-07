Place the MediaPipe FaceLandmarker task model here with the filename `face_landmarker.task`.

This repository requires a MediaPipe Tasks face-landmarker model file at `app/models/face_landmarker.task` for the selfie liveness endpoint to work.

### Obtaining the model
- Download or export a compatible MediaPipe Face Landmarker task model (task file) from MediaPipe's model resources or your own model build pipeline.
- Place the file at this path and ensure the Flask app has read access.

### Alternative path
The code will also look for the location specified by the environment variable `MEDIAPIPE_MODEL_PATH`. For example:

```powershell
$env:MEDIAPIPE_MODEL_PATH = "C:\some\other\location\face_landmarker.task"
```

If the model cannot be opened the server will raise an error on start showing the attempted path.

### Notes
- Do NOT commit the model file to version control if it contains proprietary data.
- If the directory does not exist yet, create it before placing the model.
