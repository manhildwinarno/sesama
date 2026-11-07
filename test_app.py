"""python test_app.py: worker lambat tidak menahan callback video."""
from threading import Event
from time import perf_counter
from types import SimpleNamespace

import av
import numpy as np
from video_engine import VideoEngine
from video_engine import draw_overlay


if __name__ == "__main__":
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    landmarks = (tuple((0.2, 0.5) for _ in range(21)),)
    draw_overlay(image, landmarks, False)
    assert image[50, 20].any() and not image[50, 79].any()
    image[:] = 0
    draw_overlay(image, landmarks, True)
    assert image[50, 79].any() and not image[50, 20].any()
    entered, release, closed = Event(), Event(), Event()

    class Hands:
        def process(self, image):
            entered.set()
            assert release.wait(5)
            return SimpleNamespace(multi_hand_landmarks=[])

        def close(self):
            closed.set()

    engine = VideoEngine((None, SimpleNamespace(n_features_in_=63), None), Hands)
    frame = av.VideoFrame.from_ndarray(np.zeros((48, 64, 3), dtype=np.uint8), format="bgr24")
    engine.recv(frame)
    assert entered.wait(5)
    start = perf_counter()
    for _ in range(60):
        output = engine.recv(frame)
        assert output.width == 64
    elapsed = perf_counter() - start
    assert elapsed < 1, elapsed
    with engine.condition:
        assert engine.pending is not None  # Satu slot, bukan antrean 60 frame.
    release.set()
    engine.close()
    assert closed.is_set() and not engine.thread.is_alive()
    print(f"OK: 60 callback {elapsed:.3f} detik saat worker tertahan; cleanup berhasil.")
