import io
import sys
from pathlib import Path
from time import perf_counter

import streamlit as st

# ponytail: workaround crash native ENV_001; gunakan env tanpa TensorFlow bila app membutuhkannya.
class _BlockTensorFlow:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "tensorflow" or fullname.startswith("tensorflow."):
            raise ModuleNotFoundError(fullname)
        return None


if not any(type(f).__name__ == "_BlockTensorFlow" for f in sys.meta_path):
    sys.meta_path.insert(0, _BlockTensorFlow())

import cv2
import joblib
import mediapipe as mp
import pandas as pd
from gtts import gTTS

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Isyarat · SIBI & BISINDO", layout="wide")
st.session_state.setdefault("sentence", "")
st.session_state.setdefault("camera", None)
st.session_state.setdefault("audio", None)


@st.cache_resource(max_entries=2)
def load_model(mode):
    return tuple(joblib.load(ROOT / "models" / f"{name}_{mode.lower()}.joblib")
                 for name in ("best_model", "scaler", "le"))


def stop_camera():
    camera = st.session_state.camera
    if camera:
        camera.close()
        st.session_state.camera = None


class Camera:
    """Resource lokal per sesi, bertahan ketika tombol memicu rerun."""
    def __init__(self, mode):
        self.cap = None
        self.hands = None
        self.mode = mode
        self.last = ""
        self.since = 0.0
        self.latched = False
        self.first_frame_ms = None
        self.started = perf_counter()
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_ANY)
            if not self.cap.isOpened():
                raise RuntimeError("Webcam tidak terbuka. Periksa izin kamera dan aplikasi lain.")
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.open_ms = (perf_counter() - self.started) * 1000
        except Exception:
            self.close()
            raise

    def close(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        if self.hands is not None:
            self.hands.close()
            self.hands = None

    def __del__(self):
        self.close()


def edit_sentence(action):
    text = st.session_state.sentence
    st.session_state.sentence = text + " " if action == "space" else text[:-1] if action == "delete" else ""
    st.session_state.audio = None


with st.sidebar:
    st.title("Isyarat")
    st.caption("Abjad Indonesia · Demo lokal")
    mode = st.segmented_control("Bahasa isyarat", ["SIBI", "BISINDO"], default="SIBI", key="mode")
    direction = st.radio("Arah terjemahan", ["Kamera ke teks", "Teks ke visual"])
    mirror = st.toggle("Cerminkan preview", value=True)
    with st.expander("Pengaturan deteksi"):
        flip_input = st.toggle("Balik input model", value=False,
                               help="Terpisah dari preview. Bandingkan orientasi dengan dataset pelatihan.")
        reverse_hands = st.toggle("Tukar urutan tangan BISINDO", value=False,
                                  help="Kalibrasi urutan fitur terhadap dataset; bukan jaminan kedua tangan didukung.")
        threshold = st.slider("Batas keyakinan (%)", 40, 95, 65)
        hold = st.slider("Tahan pose (detik)", 0.3, 2.0, 0.8)
    st.caption("SIBI: satu tangan · BISINDO: dua tangan")
    st.caption("Suara memakai Google TTS dan memerlukan internet.")

if st.session_state.camera and (st.session_state.camera.mode != mode or direction != "Kamera ke teks"):
    stop_camera()

st.title("Dari isyarat menjadi kata")
st.write("Peragakan abjad, tahan sebentar, lalu rangkai menjadi kalimat.")
if direction == "Teks ke visual":
    st.info("Belum tersedia. Aset abjad SIBI/BISINDO berizin dan terverifikasi masih diperlukan.")
    st.stop()


@st.fragment(run_every=0.1)
def workspace():
    left, right = st.columns([3, 2], gap="large")
    with left:
        st.subheader(f"Kamera · {mode}")
        if st.session_state.camera:
            st.button("Hentikan kamera", on_click=stop_camera, icon=":material/stop:")
        elif st.button("Aktifkan kamera", type="primary", icon=":material/videocam:"):
            try:
                with st.spinner("Membuka webcam…"):
                    st.session_state.camera = Camera(mode)
            except Exception as exc:
                st.error(str(exc))
        preview = st.empty()
        status = st.empty()
        camera = st.session_state.camera
        if camera:
            try:
                ok, raw = camera.cap.read()
                if not ok:
                    raise RuntimeError("Frame webcam tidak terbaca. Hentikan dan aktifkan kembali kamera.")
                if camera.first_frame_ms is None:
                    camera.first_frame_ms = (perf_counter() - camera.started) * 1000
                # Preview pertama dikirim sebelum inisialisasi MediaPipe dan pemuatan model.
                preview.image(cv2.flip(raw, 1) if mirror else raw, channels="BGR", width="stretch")
                if camera.hands is None:
                    status.info("Kamera aktif. Menyiapkan deteksi tangan…")
                    started = perf_counter()
                    camera.hands = mp.solutions.hands.Hands(
                        max_num_hands=1 if mode == "SIBI" else 2,
                        model_complexity=0, min_detection_confidence=0.5,
                        min_tracking_confidence=0.5)
                    camera.init_ms = (perf_counter() - started) * 1000
                started = perf_counter()
                frame = cv2.flip(raw, 1) if flip_input else raw.copy()
                result = camera.hands.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                hands = list(result.multi_hand_landmarks or [])
                for hand in hands:
                    mp.solutions.drawing_utils.draw_landmarks(frame, hand, mp.solutions.hands.HAND_CONNECTIONS)
                char, confidence = "", 0.0
                needed = 1 if mode == "SIBI" else 2
                if len(hands) == needed:
                    if reverse_hands and needed == 2:
                        hands.reverse()
                    features = [v for hand in hands for lm in hand.landmark for v in (lm.x, lm.y, lm.z)]
                    model, scaler, encoder = load_model(mode)
                    values = pd.DataFrame([features], columns=scaler.feature_names_in_) if hasattr(scaler, "feature_names_in_") else [features]
                    scaled = scaler.transform(values)
                    pred = model.predict(scaled)[0]
                    confidence = float(model.predict_proba(scaled)[0][list(model.classes_).index(pred)]) * 100
                    char = str(encoder.inverse_transform([pred])[0])
                if confidence < threshold:
                    char = ""
                now = perf_counter()
                if char != camera.last:
                    camera.last, camera.since, camera.latched = char, now, False
                if char and not camera.latched and now - camera.since >= hold:
                    st.session_state.sentence += char
                    st.session_state.audio = None
                    camera.latched = True
                progress = min((now - camera.since) / hold, 1.0) if char else 0.0
                # Inferensi dan preview memiliki orientasi independen.
                preview.image(cv2.flip(frame, 1) if mirror != flip_input else frame, channels="BGR", width="stretch")
                status.info(f"{char} · {confidence:.0f}%" if char else f"Tampilkan {needed} tangan dengan pose abjad yang jelas.")
                st.progress(progress, text="Lepaskan atau ubah pose sebelum huruf berikutnya." if camera.latched else "Tahan pose hingga stabil")
                st.caption(f"Webcam {camera.open_ms:.0f} ms · frame pertama {camera.first_frame_ms:.0f} ms · MediaPipe {camera.init_ms:.0f} ms · proses {1000*(perf_counter()-started):.0f} ms")
            except Exception as exc:
                stop_camera()
                st.error(f"Kamera dihentikan: {exc}")
        else:
            preview.info("Kamera belum aktif. Mulai saat tangan dan pencahayaan sudah siap.")
    with right:
        st.subheader("Kalimatmu")
        st.text_area("Hasil ejaan", value=st.session_state.sentence, disabled=True, height=180)
        with st.container(horizontal=True):
            st.button("Spasi", on_click=edit_sentence, args=("space",))
            st.button("Hapus", on_click=edit_sentence, args=("delete",))
            st.button("Reset", on_click=edit_sentence, args=("reset",))
        if st.button("Bunyikan suara", icon=":material/volume_up:", width="stretch"):
            if not st.session_state.sentence.strip():
                st.warning("Kalimat masih kosong.")
            else:
                try:
                    with st.spinner("Membuat suara…"):
                        audio = io.BytesIO()
                        gTTS(st.session_state.sentence, lang="id", timeout=10).write_to_fp(audio)
                        st.session_state.audio = audio.getvalue()
                except Exception as exc:
                    st.error(f"Suara gagal dibuat. Periksa internet: {exc}")
        if st.session_state.audio:
            st.audio(st.session_state.audio, format="audio/mp3", autoplay=True)
        st.caption("Untuk huruf berulang, turunkan tangan sebentar lalu peragakan kembali.")


workspace()
