"""python test_app.py: worker lambat tidak menahan callback video."""
from threading import Event
from time import perf_counter
from types import SimpleNamespace
import asyncio

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
    newest = av.VideoFrame.from_ndarray(np.full((48, 64, 3), 123, dtype=np.uint8), format="bgr24")
    output_batch = asyncio.run(engine.recv_queued([frame] * 180 + [newest]))
    assert len(output_batch) == 1
    assert (output_batch[0].to_ndarray(format="bgr24") == 123).all()
    engine.submit(av.VideoFrame.from_ndarray(np.zeros((720,1280,3),dtype=np.uint8), format="bgr24"))
    with engine.condition:
        assert engine.pending.shape == (360,640,3)
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

    # Runtime WebRTC diganti stub; tes ini menguji UI, bukan koneksi kamera browser.
    from unittest.mock import patch
    from streamlit.testing.v1 import AppTest

    class UIEngine:
        running = True

        def __init__(self, *args):
            pass

        def configure(self, *args):
            pass

        def recv(self, frame):
            return frame

        async def recv_queued(self, frames):
            return [frames[-1]]

        def close(self):
            self.running = False

        def snapshot(self):
            return {"candidate": "A", "confidence": 80, "fps": 30, "ms": 38}, []

        def overlay_snapshot(self):
            return {"points": (), "stamp": 0, "flip": False}

    with patch("video_engine.VideoEngine", UIEngine), patch("local_camera.camera"), patch("local_camera.CameraConnection"):
        app = AppTest.from_file("app.py", default_timeout=90).run()
        assert not app.exception, [e.value for e in app.exception]
        app.session_state["local-camera-SIBI"] = {"playing": True}
        app.run()
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
        print("OK: UI, catat manual, spasi/hapus/reset/audio mempertahankan engine (WebRTC stub).")
