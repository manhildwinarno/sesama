from pathlib import Path
import sys
import os
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)
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

    # Satu tangan BISINDO tetap mencapai model dan menghasilkan overlay.
    from time import sleep
    import joblib
    hand = SimpleNamespace(landmark=[SimpleNamespace(x=0.25, y=0.5, z=0.0) for _ in range(21)])

    class OneHand:
        def process(self, image):
            return SimpleNamespace(multi_hand_landmarks=[hand])

        def close(self):
            pass

    artifacts = tuple(joblib.load(f"models/{name}_bisindo.joblib")
                      for name in ("best_model", "scaler", "le"))
    overlay_engine = VideoEngine(artifacts, OneHand)
    overlay_engine.submit(np.zeros((360, 640, 3), dtype=np.uint8))
    for _ in range(200):
        points = overlay_engine.overlay_snapshot()["points"]
        if points:
            break
        sleep(0.05)
    assert points and len(points[0]) == 21 and points[0][0] == (0.25, 0.5)
    overlay_engine.close()
    print("OK: overlay 21 titik terbit dari worker.")

    # Periksa fitur sebelum scaler, urutan tangan, kandidat, dan event.
    class Scaler:
        n_features_in_ = 126

        def transform(self, values):
            np.testing.assert_array_equal(values, [expected])
            return values

    class Model:
        classes_ = [0]

        def predict(self, values):
            return [0]

        def predict_proba(self, values):
            return [[1.0]]

    encoder = SimpleNamespace(inverse_transform=lambda values: ["C"])
    second = SimpleNamespace(landmark=[SimpleNamespace(x=0.75, y=0.4, z=-0.1) for _ in range(21)])
    for detected, reverse, size in [([hand], False, 126), ([hand, second], False, 126),
                                    ([hand, second], True, 126), ([], False, 126),
                                    ([hand], False, 63)]:
        ordered = detected[::-1] if reverse else detected
        expected = [v for h in ordered for lm in h.landmark for v in (lm.x, lm.y, lm.z)]
        expected += [0.0] * (size - len(expected))
        scaler = Scaler()
        scaler.n_features_in_ = size
        scaler.feature_names_in_ = [f"f{i}" for i in range(size)]
        hands = SimpleNamespace(process=lambda image: SimpleNamespace(multi_hand_landmarks=detected),
                                close=lambda: None)
        worker = VideoEngine((Model(), scaler, encoder), lambda: hands)
        worker.configure(False, reverse, True, 65, 0)
        worker.start_diagnostic("C")
        assert 2 < worker.diagnostic_countdown() <= 3
        # Lewati waktu persiapan tanpa menunggu jam nyata.
        with worker.lock:
            worker.diagnostic_until -= 3
        try:
            worker.submit(frame)
            for _ in range(200):
                result, events = worker.snapshot()
                if "count" in result or result["error"]:
                    break
                sleep(0.05)
            assert not result["error"], result
            assert result.get("count") == len(detected), result
            assert result["candidate"] == ("C" if detected else "")
            assert events == (["C"] if detected else [])
            recording, rows = worker.diagnostic_snapshot()
            assert recording and len(rows) == 1
            assert rows[0]["label"] == "C" and rows[0]["count"] == len(detected)
            if detected:
                assert [rows[0][f"f{i}"] for i in range(size)] == expected
        finally:
            worker.close()
    print("OK: padding sebelum scaler, urutan dua tangan, tanpa tangan, event, dan SIBI.")

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

        def diagnostic_snapshot(self):
            return False, []

        def diagnostic_countdown(self):
            return 3 if hasattr(self, "label") else 0

        def start_diagnostic(self, label):
            self.label = label

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
        def radio(label):
            return next(r for r in app.radio if r.label == label)
        assert radio("Bahasa isyarat").value == "SIBI"
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
        radio("Bahasa isyarat").set_value("BISINDO").run()
        app.selectbox[0].set_value("J").run()
        resource = app.session_state["engine"]
        button("Rekam 5 detik").click().run()
        assert not app.exception and resource.label == "J"
        assert any("rekaman mulai dalam 3 detik" in item.value for item in app.info)
        assert app.session_state["engine"] is resource
        print("OK: kontrol diagnosis BISINDO mempertahankan engine.")
        radio("Mode aplikasi").set_value("Teks ke grafis").run()
        assert not resource.running and app.session_state["engine"] is None
        app.text_area(key="visual_text").set_value("IQ A!").run()
        assert not app.exception
        assert len(app.get("image")) == 3
        assert any(c.value == "Karakter belum didukung" for c in app.caption)
        radio("Bahasa grafis").set_value("SIBI").run()
        assert not app.exception and len(app.get("image")) == 0
        print("OK: grafis I/Q, placeholder SIBI/huruf hilang, dan cleanup kamera.")
