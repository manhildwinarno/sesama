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
st.set_page_config(page_title="Demo SIBI & BISINDO", layout="wide")
# ponytail: CSS terbatas pada wadah milik aplikasi; periksa setelah upgrade Streamlit.
st.html("""<style>
.st-key-workspace {max-width: 1320px; margin-inline: auto;}
.st-key-prediction [data-testid="stMetricValue"] {font-size: 3.5rem; line-height: 1.15;}
.st-key-transcript textarea:disabled {color: var(--st-text-color); -webkit-text-fill-color: var(--st-text-color); opacity: 1;}
@media (max-width: 767px) {
 .st-key-workspace [data-testid="stHorizontalBlock"] {flex-wrap: wrap;}
 .st-key-workspace [data-testid="stColumn"] {min-width: 100%;}
}
</style>""")
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


def accept_candidate():
    st.session_state.sentence += st.session_state.candidate
    st.session_state.audio = None


with st.sidebar:
    st.subheader("Pengaturan")
    st.caption("Sesuaikan deteksi tanpa mengganti model.")
    with st.expander("Orientasi input", expanded=True):
        flip = st.toggle("Balik input model", help="Mengubah gambar yang dianalisis, bukan preview. Bandingkan skor dengan pose yang sama; pilihan tangan belum otomatis.")
        reverse = st.toggle("Tukar urutan tangan BISINDO")
        st.caption("Urutan dua tangan harus sesuai data pelatihan BISINDO.")
    with st.expander("Pencatatan otomatis"):
        threshold = st.slider("Batas keyakinan (%)", 40, 95, 65,
                              help="Skor minimum sebelum huruf dicatat, bukan akurasi model.")
        hold = st.slider("Tahan pose (detik)", 0.3, 2.0, 0.5)
    with st.expander("Tentang demo"):
        st.write("Pengenalan abjad statis, bukan penerjemahan tata bahasa atau gerakan dinamis.")
        st.caption("Teks ke visual menunggu aset berizin dan pose terverifikasi. Rekaman suara belum tersedia.")

workspace = st.container(key="workspace")
with workspace:
    st.caption("ROIN · Demo lokal")
    st.title("Isyarat tangan, hasil dalam teks")
    st.write("Peragakan abjad, tahan pose, lalu rangkai kata. Mikrofon tidak digunakan.")
    mode = st.segmented_control("Bahasa isyarat", ["SIBI", "BISINDO"], default="SIBI", key="mode") or "SIBI"
engine = st.session_state.engine
if engine and st.session_state.get("engine_mode") != mode:
    engine.close()
    st.session_state.engine = None

with workspace:
    left, right = st.columns([3, 2], gap="large")
with left:
    st.subheader(f"Kamera · {mode}")
    st.caption("Satu tangan dalam bingkai." if mode == "SIBI" else "Dua tangan dalam bingkai; pastikan semua jari terlihat.")
    with st.container(horizontal=True):
        mirror = st.toggle("Cerminkan preview", value=True)
        show_landmarks = st.toggle("Titik tangan", value=False,
                                   help="Hasil pelacakan terbaru, bukan bukti prediksi benar. Bisa sedikit tertinggal saat bergerak.")
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
        key=f"camera-{mode}", queued_video_frames_callback=engine.recv_queued,
        on_video_ended=engine.close, async_processing=True,
        rtc_configuration={"iceServers": []},
        media_stream_constraints={"video": {"width": {"ideal": 640}, "height": {"ideal": 480},
                                             "frameRate": {"ideal": 30, "max": 60}}, "audio": False},
        video_html_attrs={"autoPlay": True, "controls": False, "muted": True,
                          "style": {"width": "100%"}},
    )
    st.caption("Tekan START dan izinkan kamera. Jika izin ditolak, aktifkan izin kamera pada pengaturan situs browser, lalu coba lagi.")
    with st.expander("Panduan penggunaan", icon=":material/help:"):
        st.write("1. Hadapkan telapak dan jari ke kamera dengan cahaya merata.\n2. Tahan pose sampai huruf tercatat.\n3. Lepaskan tangan sebelum mengulang huruf yang sama.")
        st.caption("Skor rendah? Periksa pose dan coba Balik input model di pengaturan. Mirror hanya mengubah preview.")


@st.fragment(run_every=0.2)
def results():
    engine = st.session_state.engine
    result, events = engine.snapshot() if engine else ({}, [])
    if events:
        st.session_state.sentence += "".join(events)
        st.session_state.audio = None
    active = bool(ctx.state.playing and engine and engine.running)
    candidate = result.get("candidate", "") if active else ""
    confidence = result.get("confidence", 0) if active else 0
    st.session_state.candidate = candidate
    with st.container(border=True, key="prediction"):
        st.metric("Huruf aktif", candidate or "—")
        st.progress(min(1.0, max(0.0, confidence / 100)),
                    text=f"Keyakinan {confidence:.1f}% · ambang {threshold}%")
        if not active:
            status = "Kamera belum aktif · tekan START"
        elif not candidate:
            status = "Menunggu pose · pastikan jumlah tangan sesuai mode"
        elif confidence < threshold:
            status = "Skor belum cukup · sesuaikan pose"
        else:
            status = f"Tahan pose {hold:.1f} detik · lepaskan tangan untuk mengulang"
        st.caption(status)
    if events:
        st.caption(f"Huruf tercatat: {', '.join(events)}")
    if result.get("error"):
        st.error(result["error"])
    st.subheader("Hasil ejaan")
    with st.container(key="transcript"):
        st.text_area("Teks hasil pengenalan", value=st.session_state.sentence, disabled=True, height=130,
                     placeholder="Huruf yang diterima muncul di sini.")
    with st.container(horizontal=True):
        st.button("Spasi", on_click=edit_sentence, args=("space",), disabled=not st.session_state.sentence)
        st.button("Hapus", on_click=edit_sentence, args=("delete",), disabled=not st.session_state.sentence)
        st.button("Reset", on_click=edit_sentence, args=("reset",), disabled=not st.session_state.sentence)
    st.button("Catat manual", disabled=not candidate, on_click=accept_candidate,
              help="Melewati ambang; periksa huruf sebelum mencatat.")
    if st.button("Bunyikan teks", icon=":material/volume_up:", width="stretch", type="primary",
                 disabled=not st.session_state.sentence.strip()):
        if not st.session_state.sentence.strip():
            st.warning("Kalimat masih kosong.")
        else:
            try:
                audio = io.BytesIO()
                with st.spinner("Menyiapkan suara…"):
                    gTTS(st.session_state.sentence, lang="id", timeout=10).write_to_fp(audio)
                st.session_state.audio = audio.getvalue()
            except Exception as exc:
                st.error(f"Suara gagal: {exc}")
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3", autoplay=True)
    st.caption("Suara memerlukan internet. Teks dikirim ke Google saat Bunyikan teks ditekan.")
    with st.expander("Diagnostik", icon=":material/speed:"):
        st.caption(f"Video masuk {result.get('fps', 0) if active else 0:.1f} FPS · inferensi {result.get('ms', 0) if active else 0:.0f} ms")
        st.caption("FPS mengukur callback masuk, bukan render browser. Kelancaran bergantung perangkat dan cahaya.")


with right:
    results()
