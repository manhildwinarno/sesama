"""python test_camera.py: server frame loopback menerima JPEG tanpa browser."""
import urllib.error
import urllib.request

import cv2
import numpy as np
from local_camera import FrameServer


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
