"""python test_app.py: antrean frame terbaru dan regresi UI tanpa kamera nyata."""
from threading import Event
from time import perf_counter
from types import SimpleNamespace

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
    frame = np.zeros((48, 64, 3), dtype=np.uint8)
    engine.submit(frame)
    assert entered.wait(5)
    engine.submit(np.zeros((720, 1280, 3), dtype=np.uint8))
    with engine.condition:
        assert engine.pending.shape == (360, 640, 3)
    start = perf_counter()
    for _ in range(60):
        engine.submit(np.full((48, 64, 3), 123, dtype=np.uint8))
    elapsed = perf_counter() - start
    assert elapsed < 1, elapsed
    with engine.condition:
        assert engine.pending is not None  # Satu slot, bukan antrean 60 frame.
        assert (engine.pending == 123).all()
        assert engine.pending.shape == (48, 64, 3)
    release.set()
    engine.close()
    assert closed.is_set() and not engine.thread.is_alive()
    print(f"OK: 60 submit {elapsed:.3f} detik saat worker tertahan; cleanup berhasil.")

    # Overlay harus terbit walau model tidak dipanggil (2 tangan dibutuhkan, 1 terdeteksi).
    from time import sleep
    hand = SimpleNamespace(landmark=[SimpleNamespace(x=0.25, y=0.5) for _ in range(21)])

    class OneHand:
        def process(self, image):
            return SimpleNamespace(multi_hand_landmarks=[hand])

        def close(self):
            pass

    overlay_engine = VideoEngine((None, SimpleNamespace(n_features_in_=126), None), OneHand)
    overlay_engine.submit(np.zeros((360, 640, 3), dtype=np.uint8))
    for _ in range(40):
        points = overlay_engine.overlay_snapshot()["points"]
        if points:
            break
        sleep(0.05)
    assert points and len(points[0]) == 21 and points[0][0] == (0.25, 0.5)
    overlay_engine.close()
    print("OK: overlay 21 titik terbit dari worker.")

    # Kamera browser dan server HTTP diganti stub; ini tes UI, bukan izin kamera.
    from unittest.mock import patch
    from streamlit.testing.v1 import AppTest

    class UIEngine:
        running = True

        def __init__(self, *args):
            pass

        def configure(self, *args):
            pass

        def close(self):
            self.running = False

        def snapshot(self):
            return {"candidate": "A", "confidence": 80, "fps": 30, "ms": 38, "active": True}, []

        def overlay_snapshot(self):
            return {"points": (), "stamp": 0, "flip": False}

    class UIServer:
        url = "http://127.0.0.1:9/frame"

        def register(self, token, engine):
            pass

        def unregister(self, token):
            pass

    with patch("video_engine.VideoEngine", UIEngine), patch("local_camera.camera"), \
         patch("local_camera.get_frame_server", return_value=UIServer()):
        app = AppTest.from_file("app.py", default_timeout=90).run()
        assert not app.exception, [e.value for e in app.exception]
        assert app.radio[0].value == "SIBI"
        resource = app.session_state["engine"]
        def button(label):
            return next(b for b in app.button if b.label == label)
        button("Catat manual").click().run()
        assert app.session_state["sentence"] == "A"
        button("Spasi").click().run()
        assert app.session_state["sentence"] == "A "
        button("Hapus").click().run()
        assert app.session_state["sentence"] == "A"
        with patch("gtts.gTTS") as speech:
            button("Bunyikan teks").click().run()
            speech.assert_called_once_with("A", lang="id", timeout=10)
        button("Reset").click().run()
        assert app.session_state["sentence"] == ""
        assert app.session_state["engine"] is resource and resource.running
        assert not app.exception, [e.value for e in app.exception]
        print("OK: UI, catat manual, spasi/hapus/reset/audio mempertahankan engine (kamera stub).")
