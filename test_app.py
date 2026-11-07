"""Jalankan dengan Python ENV_001; tidak mengakses webcam atau internet."""
from pathlib import Path
from streamlit.testing.v1 import AppTest


class FakeCamera:
    mode = "SIBI"
    closed = False
    cap = None

    def close(self):
        self.closed = True


if __name__ == "__main__":
    app = AppTest.from_file(str(Path(__file__).with_name("app.py")), default_timeout=90).run()
    assert not app.exception
    # Resource tetap sama pada rerun tombol; read() palsu mengembalikan frame kosong.
    import numpy as np
    from types import SimpleNamespace

    camera = FakeCamera()
    camera.cap = SimpleNamespace(read=lambda: (True, np.zeros((8, 8, 3), dtype=np.uint8)))
    camera.hands = SimpleNamespace(process=lambda frame: SimpleNamespace(multi_hand_landmarks=[]))
    camera.first_frame_ms = camera.open_ms = camera.init_ms = 0
    camera.last, camera.since, camera.latched = "", 0, False
    app.session_state["camera"] = camera
    app.session_state["sentence"] = "AB"
    app.run()
    for label, expected in [("Spasi", "AB "), ("Hapus", "AB"), ("Reset", ""), ("Bunyikan suara", "")]:
        next(button for button in app.button if button.label == label).click().run()
        assert not app.exception, [e.value for e in app.exception]
        assert app.session_state["camera"] is camera and not camera.closed
        assert app.session_state["sentence"] == expected
    next(button for button in app.button if button.label == "Hentikan kamera").click().run()
    assert camera.closed and app.session_state["camera"] is None
    print("OK: tombol mempertahankan kamera; stop menutup resource.")
