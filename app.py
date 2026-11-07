import io
import sys
from pathlib import Path

import streamlit as st

# ponytail: workaround crash native ENV_001; evaluasi env terpisah jika TF dibutuhkan.
class _BlockTensorFlow:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "tensorflow" or fullname.startswith("tensorflow."):
            raise ModuleNotFoundError(fullname)


if not any(type(f).__name__ == "_BlockTensorFlow" for f in sys.meta_path):
    sys.meta_path.insert(0, _BlockTensorFlow())

import joblib
import mediapipe as mp
from gtts import gTTS
from streamlit_webrtc import webrtc_streamer
from video_engine import VideoEngine

ROOT = Path(__file__).resolve().parent
st.set_page_config(page_title="Isyarat · SIBI & BISINDO", layout="wide")
for key, value in {"sentence": "", "audio": None, "engine": None, "candidate": ""}.items():
    st.session_state.setdefault(key, value)


@st.cache_resource(max_entries=2)
def load_model(mode):
    return tuple(joblib.load(ROOT / "models" / f"{name}_{mode.lower()}.joblib")
                 for name in ("best_model", "scaler", "le"))


def edit_sentence(action):
    text = st.session_state.sentence
    st.session_state.sentence = text + " " if action == "space" else text[:-1] if action == "delete" else ""
    st.session_state.audio = None


with st.sidebar:
    st.title("Isyarat")
    st.caption("Abjad Indonesia · Demo lokal")
    mode = st.segmented_control("Bahasa isyarat", ["SIBI", "BISINDO"], default="SIBI", key="mode") or "SIBI"
    direction = st.radio("Arah terjemahan", ["Kamera ke teks", "Teks ke visual"])
    mirror = st.toggle("Cerminkan preview", value=True)
    show_landmarks = st.toggle("Tampilkan titik tangan", value=False,
                               help="Overlay hasil deteksi terbaru; bisa sedikit tertinggal saat bergerak cepat. Bukan indikator prediksi benar.")
    with st.expander("Pengaturan deteksi"):
        flip = st.toggle("Balik input model", help="Terpisah dari orientasi preview.")
        reverse = st.toggle("Tukar urutan tangan BISINDO")
        threshold = st.slider("Batas keyakinan (%)", 40, 95, 65,
                              help="Skor minimum sebelum huruf dicatat, bukan akurasi model.")
        hold = st.slider("Tahan pose (detik)", 0.3, 2.0, 0.5)
    st.caption("Suara membutuhkan internet dan mengirim teks ke Google.")

st.title("Dari isyarat menjadi kata")
st.write("Peragakan abjad dan tahan pose sebentar. Lepaskan tangan untuk mengulang huruf.")
engine = st.session_state.engine
if engine and (st.session_state.get("engine_mode") != mode or direction != "Kamera ke teks"):
    engine.close()
    st.session_state.engine = None
if direction != "Kamera ke teks":
    st.info("Teks ke visual belum tersedia; aset berizin dan pose terverifikasi diperlukan.")
    st.stop()

left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader(f"Kamera · {mode}")
    # Factory dipanggil worker; tidak memanggil st.* dari thread video/inferensi.
    def create_engine():
        engine = VideoEngine(load_model(mode), lambda: mp.solutions.hands.Hands(
            max_num_hands=1 if mode == "SIBI" else 2,
            model_complexity=1, min_detection_confidence=0.5, min_tracking_confidence=0.5))
        st.session_state.engine = engine
        st.session_state.engine_mode = mode
        return engine

    engine = st.session_state.engine
    if engine is None or not engine.running:
        engine = create_engine()
    engine.configure(flip, reverse, mirror, threshold, hold, show_landmarks)
    ctx = webrtc_streamer(
        key=f"camera-{mode}", video_frame_callback=engine.recv,
        on_video_ended=engine.close, async_processing=False,
        rtc_configuration={"iceServers": []},
        media_stream_constraints={"video": {"width": {"ideal": 640}, "height": {"ideal": 480},
                                             "frameRate": {"ideal": 30, "max": 60}}, "audio": False},
        video_html_attrs={"autoPlay": True, "controls": False, "muted": True,
                          "style": {"width": "100%"}},
    )
    st.caption("Tekan START dan izinkan kamera di browser. Mikrofon tidak digunakan. Target 30 FPS; tergantung perangkat.")


@st.fragment(run_every=0.2)
def results():
    engine = st.session_state.engine
    result, events = engine.snapshot() if engine else ({}, [])
    if events:
        st.session_state.sentence += "".join(events)
        st.session_state.audio = None
    candidate = result.get("candidate", "")
    st.session_state.candidate = candidate
    st.subheader("Kalimatmu")
    st.caption(f"Prediksi: {candidate or '—'} · skor {result.get('confidence', 0):.1f}% · ambang {threshold}%")
    st.caption(f"Video masuk {result.get('fps', 0):.1f} FPS · inferensi {result.get('ms', 0):.0f} ms")
    if result.get("error"):
        st.error(result["error"])
    st.text_area("Hasil ejaan", value=st.session_state.sentence, disabled=True, height=180)
    with st.container(horizontal=True):
        st.button("Spasi", on_click=edit_sentence, args=("space",))
        st.button("Hapus", on_click=edit_sentence, args=("delete",))
        st.button("Reset", on_click=edit_sentence, args=("reset",))
    if st.button("Catat prediksi sekarang", disabled=not candidate,
                 help="Melewati ambang; periksa huruf sebelum mencatat."):
        st.session_state.sentence += candidate
        st.session_state.audio = None
        st.rerun(scope="fragment")
    if st.button("Bunyikan suara", icon=":material/volume_up:", width="stretch"):
        if not st.session_state.sentence.strip():
            st.warning("Kalimat masih kosong.")
        else:
            try:
                audio = io.BytesIO()
                gTTS(st.session_state.sentence, lang="id", timeout=10).write_to_fp(audio)
                st.session_state.audio = audio.getvalue()
            except Exception as exc:
                st.error(f"Suara gagal: {exc}")
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3", autoplay=True)


with right:
    results()
