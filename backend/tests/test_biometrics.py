import numpy as np
import pytest
from app.routes import biometrics


class DummyResult:
    def __init__(self, landmarks):
        # landmarks is whatever face_landmarks should be
        self.face_landmarks = [landmarks]


def make_fake_mesh_object():
    class FakeLM:
        def __init__(self, x, y):
            self.x = x
            self.y = y

    return [FakeLM(0.1, 0.2) for _ in range(470)]


def make_fake_mesh_list():
    return [[0.1, 0.2] for _ in range(470)]


def test_extract_handles_object_list(monkeypatch):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    fake_mesh = make_fake_mesh_object()
    dummy = DummyResult(fake_mesh)
    class FakeFL:
        def detect(self, img):
            return dummy
    monkeypatch.setattr(biometrics, 'face_landmarker', FakeFL())
    res = biometrics.extract_eye_landmarks(img)
    assert res is not None
    left, right, mesh = res
    # results should be 6 points each
    assert left.shape == (6, 2)
    assert right.shape == (6, 2)
    assert len(mesh) == 470


def test_extract_handles_plain_list(monkeypatch):
    img = np.zeros((480, 640, 3), dtype=np.uint8)
    fake_mesh = make_fake_mesh_list()
    dummy = DummyResult(fake_mesh)
    class FakeFL:
        def detect(self, img):
            return dummy
    monkeypatch.setattr(biometrics, 'face_landmarker', FakeFL())
    res = biometrics.extract_eye_landmarks(img)
    assert res is not None
    left, right, mesh = res
    assert left.shape == (6, 2)
    assert right.shape == (6, 2)
    assert len(mesh) == 470


def test_selfie_landmark_format_error(monkeypatch, tmp_path):
    """If the landmark parser raises ValueError, the route returns 400."""
    # prepare a tiny dummy image file
    import cv2
    img_path = tmp_path / "img.jpg"
    cv2.imwrite(str(img_path), np.zeros((10, 10, 3), dtype=np.uint8))

    # monkeypatch extraction to throw
    def bad(image_array):
        raise ValueError("broken format")
    monkeypatch.setattr(biometrics, 'extract_eye_landmarks', bad)

    from app.main import create_app
    app = create_app()
    client = app.test_client()
    with open(img_path, 'rb') as f:
        resp = client.post(
            '/api/biometrics/selfie',
            data={'voter_id': '123e4567-e89b-12d3-a456-426614174000', 'image': f},
        )
    assert resp.status_code == 400
    body = resp.get_json()
    assert 'Face landmark format error' in body.get('message', '')
