import sys

# Mencegah crash native C++ TensorFlow di Windows saat runtime Streamlit.
# Model proyek menggunakan SVM (scikit-learn), TensorFlow tidak dibutuhkan.
# MediaPipe mengimpor TensorFlow hanya secara opsional untuk docgen.
class _BlockTensorFlow:
    def find_spec(self, fullname, path=None, target=None):
        if fullname == "tensorflow" or fullname.startswith("tensorflow."):
            raise ModuleNotFoundError(f"tensorflow dinonaktifkan: {fullname}")
        return None

if not any(isinstance(f, _BlockTensorFlow) for f in sys.meta_path):
    sys.meta_path.insert(0, _BlockTensorFlow())

import streamlit as st
import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
import joblib
import time
import base64
from gtts import gTTS
import io

# -------------------------------------------------------------
# KONFIGURASI HALAMAN STREAMLIT
# -------------------------------------------------------------
st.set_page_config(
    page_title="Penerjemah Bahasa Isyarat (SIBI & BISINDO)",
    page_icon="🤟",
    layout="wide"
)

# -------------------------------------------------------------
# LOAD MODEL & PREPROCESSING PIPELINE
# -------------------------------------------------------------
@st.cache_resource
def load_all_models():
    models = {
        "sibi": {
            "model": joblib.load("models/best_model_sibi.joblib"),
            "scaler": joblib.load("models/scaler_sibi.joblib"),
            "encoder": joblib.load("models/le_sibi.joblib")
        },
        "bisindo": {
            "model": joblib.load("models/best_model_bisindo.joblib"),
            "scaler": joblib.load("models/scaler_bisindo.joblib"),
            "encoder": joblib.load("models/le_bisindo.joblib")
        }
    }
    return models

try:
    resources = load_all_models()
    models_ready = True
except Exception as e:
    models_ready = False
    st.error(f"Gagal memuat model: {e}. Pastikan seluruh file .joblib ada di dalam folder 'models/'!")

# Inisialisasi MediaPipe Hands & Drawing
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils

# Inisialisasi Session State untuk Kalimat
if "sentence" not in st.session_state:
    st.session_state.sentence = ""


def scale_features(scaler, features):
    """Transform fitur; gunakan nama kolom jika scaler dilatih dari DataFrame."""
    if hasattr(scaler, "feature_names_in_"):
        return scaler.transform(pd.DataFrame([features], columns=scaler.feature_names_in_))
    return scaler.transform([features])

def speak_text(text):
    if not text.strip():
        return
    try:
        tts = gTTS(text=text, lang='id')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        audio_bytes = fp.read()
        b64 = base64.b64encode(audio_bytes).decode()
        audio_html = f'<audio autoplay="true" src="data:audio/mp3;base64,{b64}"></audio>'
        st.markdown(audio_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Gagal membuat suara: {e}. Fitur suara membutuhkan koneksi internet.")

# -------------------------------------------------------------
# SIDEBAR PENGATURAN
# -------------------------------------------------------------
with st.sidebar:
    st.title("⚙️ Pengaturan Sistem")
    mode = st.radio(
        "Pilih Bahasa Isyarat:",
        ("SIBI (1 Tangan)", "BISINDO (2 Tangan)"),
        help="SIBI menggunakan 1 tangan (63 koordinat), BISINDO menggunakan 2 tangan (126 koordinat)."
    )
    
    st.divider()
    st.subheader("Informasi Model Aktif")
    if "SIBI" in mode:
        st.info("**Mode:** SIBI Abjad\n\n**Algoritma:** SVM (RBF Kernel)\n\n**Akurasi Uji:** 95.92%")
    else:
        st.info("**Mode:** BISINDO Abjad\n\n**Algoritma:** SVM (RBF Kernel)\n\n**Akurasi Uji:** 95.95%")
        
    st.divider()
    st.caption("Mata Kuliah: Pembelajaran Mesin | IPB University")

# -------------------------------------------------------------
# TAMPILAN UTAMA
# -------------------------------------------------------------
st.title("🤟 Penerjemah Bahasa Isyarat Interaktif")
st.markdown("Penerjemah Abjad **SIBI & BISINDO** berbasis **Machine Learning (Support Vector Machine)** dengan pelacakan *landmark* MediaPipe secara *real-time*.")

col_cam, col_text = st.columns([3, 2])

# Kolom Kanan: Papan Teks & Audio
with col_text:
    st.subheader("📝 Teks Terjemahan")
    
    # Text Area Teks yang Sedang Dirangkai
    # Catatan: JANGAN memberi key pada widget ini. Jika key + value dipakai bersamaan,
    # Streamlit memakai nilai lama dari widget state dan perubahan kalimat tidak tampil.
    sentence_slot = st.empty()
    sentence_slot.text_area("Kalimat:", value=st.session_state.sentence, height=120, disabled=True)
    
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("➕ Spasi", width="stretch"):
            st.session_state.sentence += " "
            st.rerun()
    with col_btn2:
        if st.button("⌫ Hapus", width="stretch"):
            st.session_state.sentence = st.session_state.sentence[:-1]
            st.rerun()
    with col_btn3:
        if st.button("🗑️ Reset", width="stretch"):
            st.session_state.sentence = ""
            st.rerun()
            
    st.write("")
    if st.button("🔊 Bunyikan Suara (Voice Over)", type="primary", width="stretch"):
        if st.session_state.sentence.strip():
            speak_text(st.session_state.sentence)
        else:
            st.warning("Teks masih kosong!")

# Kolom Kiri: Layar Kamera
with col_cam:
    st.subheader("📹 Umpan Kamera Langsung")
    start_cam = st.toggle("Aktifkan Kamera Webcam", value=False)
    frame_placeholder = st.empty()
    status_placeholder = st.empty()

# -------------------------------------------------------------
# PIPELINE INFERENSI KAMERA REAL-TIME
# -------------------------------------------------------------
if start_cam and models_ready:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error(
            "Webcam tidak dapat dibuka. Pastikan kamera tidak sedang dipakai aplikasi lain "
            "dan izin akses kamera sudah aktif."
        )
    else:
        # Konfigurasi Tangan sesuai Mode
        max_hands = 1 if "SIBI" in mode else 2
        hands = mp_hands.Hands(
            min_detection_confidence=0.7,
            min_tracking_confidence=0.7,
            max_num_hands=max_hands
        )

        current_key = "sibi" if "SIBI" in mode else "bisindo"
        active_model = resources[current_key]["model"]
        active_scaler = resources[current_key]["scaler"]
        active_encoder = resources[current_key]["encoder"]

        last_pred = ""
        pred_count = 0
        COOLDOWN_FRAMES = 12  # Jumlah frame stabil sebelum huruf otomatis tercatat

        try:
            while cap.isOpened() and start_cam:
                ret, frame = cap.read()
                if not ret:
                    st.error("Gagal membaca umpan webcam!")
                    break

                frame = cv2.flip(frame, 1)  # Cermin horizontal
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = hands.process(frame_rgb)

                detected_char = ""
                confidence = 0.0

                if results.multi_hand_landmarks:
                    for hand_landmarks in results.multi_hand_landmarks:
                        mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # SIBI MODE (1 Tangan = 63 fitur)
                    if current_key == "sibi":
                        lms = results.multi_hand_landmarks[0]
                        features = []
                        for lm in lms.landmark:
                            features.extend([lm.x, lm.y, lm.z])

                        # Transform & Predict
                        feat_scaled = scale_features(active_scaler, features)
                        pred_idx = active_model.predict(feat_scaled)[0]
                        probs = active_model.predict_proba(feat_scaled)[0]
                        detected_char = active_encoder.inverse_transform([pred_idx])[0]
                        confidence = probs[pred_idx] * 100

                    # BISINDO MODE (2 Tangan = 126 fitur)
                    elif current_key == "bisindo":
                        if len(results.multi_hand_landmarks) == 2:
                            features = []
                            # Ambil landmark tangan pertama dan kedua
                            for hand_lms in results.multi_hand_landmarks:
                                for lm in hand_lms.landmark:
                                    features.extend([lm.x, lm.y, lm.z])

                            feat_scaled = scale_features(active_scaler, features)
                            pred_idx = active_model.predict(feat_scaled)[0]
                            probs = active_model.predict_proba(feat_scaled)[0]
                            detected_char = active_encoder.inverse_transform([pred_idx])[0]
                            confidence = probs[pred_idx] * 100
                        else:
                            status_placeholder.warning("⚠️ BISINDO membutuhkan kedua tangan di depan kamera!")

                    # Tampilkan Overlay Teks di Video
                    if detected_char and confidence > 65.0:
                        cv2.putText(frame, f"Huruf: {detected_char} ({confidence:.1f}%)", (30, 60),
                                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)

                        # Logika Debounce/Akumulasi Huruf Otomatis
                        if detected_char == last_pred:
                            pred_count += 1
                            if pred_count == COOLDOWN_FRAMES:
                                st.session_state.sentence += detected_char
                                # Tampilkan huruf baru segera tanpa menunggu rerun
                                sentence_slot.text_area(
                                    "Kalimat:",
                                    value=st.session_state.sentence,
                                    height=120,
                                    disabled=True,
                                )
                                pred_count = 0
                        else:
                            last_pred = detected_char
                            pred_count = 0
                    else:
                        pred_count = 0
                else:
                    status_placeholder.info("Arahkan tangan ke kamera untuk mulai menerjemahkan.")
                    pred_count = 0

                frame_placeholder.image(frame, channels="BGR", width="stretch")
                time.sleep(0.02)
        finally:
            cap.release()
            hands.close()