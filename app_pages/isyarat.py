import io
import math
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
import pandas as pd
import mediapipe as mp
from gtts import gTTS
from local_camera import camera, get_frame_server, new_token
from video_engine import VideoEngine

ROOT = Path(__file__).resolve().parents[1]


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


workspace = st.container(key="workspace")
with workspace:
    st.caption("RUANG BELAJAR / ISYARAT KE TEKS")
    heading, language = st.columns([3, 1], vertical_alignment="center")
    with heading:
        st.title("Dari isyarat, menjadi kata.")
        st.caption("Peragakan abjad, tahan pose, lalu rangkai kata. Mikrofon tidak digunakan.")
    with language:
        mode = st.segmented_control("Bahasa isyarat", ["SIBI", "BISINDO"], default="SIBI", required=True, key="mode", persist_state="session")
    with st.expander("Pengaturan pencatatan", icon=":material/tune:"):
        threshold = st.slider("Batas keyakinan (%)", 40, 95, 65, key="threshold", persist_state="session",
                              help="Skor minimum sebelum huruf dicatat, bukan akurasi model.")
        hold = st.slider("Tahan pose (detik)", 0.2, 2.0, 0.4, key="hold", persist_state="session")
    with st.expander("Pengaturan lanjutan", icon=":material/settings:"):
        flip = st.toggle("Balik input model", key="flip", persist_state="session", help="Mengubah gambar inferensi, bukan preview. Bukan koreksi otomatis.")
        reverse = st.toggle("Tukar urutan tangan BISINDO", disabled=mode != "BISINDO", key="reverse", persist_state="session")
        st.caption("Urutan harus cocok data pelatihan. Perubahan bisa memperburuk hasil.")
engine = st.session_state.engine
server = get_frame_server()
token = st.session_state.setdefault("frame_token", new_token())
if engine and st.session_state.get("engine_mode") != mode:
    server.unregister(token)
    engine.close()
    st.session_state.engine = None

with workspace:
    left, right = st.columns([3, 2], gap="large")
with left, st.container(border=True, key="camera-card"):
    st.subheader(f"Kamera · {mode}")
    st.caption("Satu tangan dalam bingkai." if mode == "SIBI" else "Satu atau dua tangan sesuai abjad; pastikan semua jari terlihat.")
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
    engine.configure(flip, reverse if mode == "BISINDO" else False, mirror, threshold, hold, show_landmarks)
    server.register(token, engine)

    camera(key=f"local-camera-{mode}", data={
        "url": server.url, "token": token, "mirror": mirror,
        "show": show_landmarks,
    })
    st.caption("Tekan START dan izinkan kamera. Jika izin ditolak, aktifkan izin kamera pada pengaturan situs browser, lalu coba lagi.")
    with st.expander("Panduan penggunaan", icon=":material/help:"):
        st.write("1. Hadapkan telapak dan jari ke kamera dengan cahaya merata.\n2. Tahan pose sampai huruf tercatat.\n3. Lepaskan tangan sebelum mengulang huruf yang sama.")
        st.caption("Skor rendah? Periksa pose dan coba Balik input model di pengaturan. Mirror hanya mengubah preview.")


@st.fragment(run_every=0.3)
def results():
    engine = st.session_state.engine
    result, events = engine.snapshot() if engine else ({}, [])
    if events:
        st.session_state.sentence += "".join(events)
        st.session_state.audio = None
    active = bool(result.get("active") and engine and engine.running)
    candidate = result.get("candidate", "") if active else ""
    confidence = result.get("confidence", 0) if active else 0
    st.session_state.candidate = candidate
    with st.container(border=True, key="prediction"):
        st.metric("Huruf aktif", candidate or "—")
        st.progress(min(1.0, max(0.0, confidence / 100)),
                    text=f"Keyakinan {confidence:.1f}% · ambang {threshold}%")
        if not active:
            status = "Menunggu frame kamera · tekan START"
        elif not candidate:
            status = "Menunggu pose · belum ada input tangan yang dapat diklasifikasikan"
        elif confidence < threshold:
            status = "Skor belum cukup · sesuaikan pose"
        else:
            status = f"Tahan pose {hold:.1f} detik · lepaskan tangan untuk mengulang"
        st.caption(status)
        if active and "count" in result:
            st.caption(f"Terdeteksi {result['count']} tangan · " +
                       ("model dijalankan" if candidate else "belum ada kandidat"))
    if events:
        st.caption(f"Huruf tercatat: {', '.join(events)}")
    if result.get("error"):
        st.error(result["error"])
    with st.container(border=True, key="transcript"):
        st.subheader("Hasil ejaan")
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
        ago = result.get("ago")
        age = f"{ago:.1f} detik lalu" if ago is not None else "belum ada"
        st.caption(f"Frame terakhir {age} · {result.get('fps', 0) if active else 0:.1f} FPS · inferensi {result.get('ms', 0) if active else 0:.0f} ms")
        st.caption("FPS mengukur frame yang diterima Python, bukan render preview browser. Preview memakai kamera lokal.")
    if mode == "BISINDO":
        with st.expander("Rekam sampel diagnosis"):
            label = st.selectbox("Huruf yang diperagakan", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
            st.caption("Setelah ditekan, tersedia 3 detik untuk menyiapkan pose. Rekaman berlangsung 5 detik, tanpa gambar. Unduh sebelum merekam ulang atau mengganti mode.")
            recording, rows = engine.diagnostic_snapshot()
            if st.button("Rekam 5 detik", disabled=recording or not active):
                engine.start_diagnostic(label)
                recording, rows = True, []
            countdown = engine.diagnostic_countdown()
            if countdown > 0:
                st.info(f"Siapkan pose · rekaman mulai dalam {math.ceil(countdown)} detik")
            else:
                st.caption(f"{'Merekam' if recording else 'Siap'} · {len(rows)} sampel")
            if rows and not recording:
                st.download_button("Unduh CSV diagnosis", pd.DataFrame(rows).to_csv(index=False),
                                   file_name=f"bisindo_{rows[0]['label']}_diagnosis.csv", mime="text/csv")


with right:
    results()
