"""python test_camera.py: server frame loopback sampai worker inferensi nyata."""
import urllib.error
import urllib.request
from time import sleep
from types import SimpleNamespace

import cv2
import numpy as np
from local_camera import FrameServer
from video_engine import VideoEngine


def post(url, token, body, origin=None):
    request = urllib.request.Request(url, data=body, method="POST", headers={
        "Content-Type": "image/jpeg", "X-Frame-Token": token,
        **({"Origin": origin} if origin else {}),
    })
    try:
        with urllib.request.urlopen(request, timeout=5) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


if __name__ == "__main__":
    class Engine:
        def __init__(self):
            self.image = None

        def submit(self, image):
            self.image = image

    server, engine = FrameServer(), Engine()
    server.register("token", engine)
    ok, encoded = cv2.imencode(".jpg", np.full((360, 640, 3), 123, dtype=np.uint8))
    assert ok
    assert post(server.url, "token", encoded.tobytes()) == 204
    assert engine.image is not None and engine.image.shape == (360, 640, 3)
    assert (engine.image == 123).all()
    assert post(server.url, "wrong", encoded.tobytes()) == 403
    assert post(server.url, "token", encoded.tobytes(), "https://example.com") == 403
    assert post(server.url, "token", b"not a jpeg") == 400
    server.unregister("token")
    assert post(server.url, "token", encoded.tobytes()) == 403
    print("OK: JPEG loopback diterima; token, origin, dan isi rusak ditolak.")

    # Jalur penuh: JPEG loopback -> VideoEngine -> status/overlay.
    hand = SimpleNamespace(landmark=[SimpleNamespace(x=0.25, y=0.5) for _ in range(21)])

    class Hands:
        def process(self, image):
            return SimpleNamespace(multi_hand_landmarks=[hand])

        def close(self):
            pass

    engine = VideoEngine((None, SimpleNamespace(n_features_in_=126), None), Hands)
    server.register("real", engine)
    assert post(server.url, "real", encoded.tobytes()) == 204
    for _ in range(40):
        result, _ = engine.snapshot()
        points = engine.overlay_snapshot()["points"]
        if result["active"] and points:
            break
        sleep(0.05)
    assert result["active"], result
    assert points and points[0][0] == (0.25, 0.5)
    engine.close()
    print("OK: frame HTTP membuat engine aktif dan overlay 21 titik terbit.")
