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
    settings, center, right = st.columns([1.05, 3.2, 1.4], gap="small")
with settings:
    with st.container(border=True, key="settings-card"):
        st.subheader("Recognition")
        mode = st.segmented_control("Sign language", ["SIBI", "BISINDO"], default="SIBI", required=True, key="mode", persist_state="session")
        threshold = st.slider("Confidence (%)", 40, 95, 65, key="threshold", persist_state="session",
                              help="Minimum score for automatic capture; not model accuracy.")
        hold = st.slider("Hold duration (s)", 0.2, 2.0, 0.4, key="hold", persist_state="session")
        with st.expander("Advanced", icon=":material/settings:"):
            flip = st.toggle("Flip model input", key="flip", persist_state="session", help="Changes inference input, not preview. Not an automatic correction.")
            reverse = st.toggle("Swap BISINDO hands", disabled=mode != "BISINDO", key="reverse", persist_state="session", help="Hand order must match training; changing it may reduce accuracy.")
engine = st.session_state.engine
server = get_frame_server()
token = st.session_state.setdefault("frame_token", new_token())
if engine and st.session_state.get("engine_mode") != mode:
    server.unregister(token)
    engine.close()
    st.session_state.engine = None

with center, st.container(key="camera-stage"):
    preview = st.container()
    mirror = st.session_state.get("preview_mirror", True)
    show_landmarks = st.session_state.get("preview_landmarks", False)
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

    with preview:
        camera_key = f"local-camera-{mode}"
        def camera_options():
            state = st.session_state[camera_key]
            st.session_state.preview_mirror = state.mirror
            st.session_state.preview_landmarks = state.show
        camera(key=f"local-camera-{mode}", data={
            "url": server.url, "token": token, "mirror": mirror,
            "show": show_landmarks,
        }, default={"mirror": mirror, "show": show_landmarks}, on_mirror_change=camera_options, on_show_change=camera_options)


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
        st.metric("Current letter", candidate or "—")
        st.progress(min(1.0, max(0.0, confidence / 100)),
                    text=f"Confidence {confidence:.1f}%")
        if not active:
            status = "Camera off"
        elif not candidate:
            status = "Waiting for a hand"
        elif confidence < threshold:
            status = "Adjust your pose"
        else:
            status = f"Hold for {hold:.1f}s · release to repeat"
        st.caption(status)
    if events:
        st.caption(f"Captured: {', '.join(events)}")
    if result.get("error"):
        st.error(result["error"])
    with st.container(border=True, key="transcript"):
        st.subheader("Transcript")
        st.text_area("Recognized text", value=st.session_state.sentence, disabled=True, height=100, label_visibility="collapsed",
                     placeholder="Your letters appear here")
    with st.container(horizontal=True):
        st.button("Space", on_click=edit_sentence, args=("space",), disabled=not st.session_state.sentence)
        st.button("Delete", on_click=edit_sentence, args=("delete",), disabled=not st.session_state.sentence)
        st.button("Reset", on_click=edit_sentence, args=("reset",), disabled=not st.session_state.sentence)
    st.button("Capture letter", disabled=not candidate, on_click=accept_candidate,
              help="Bypasses confidence threshold. Check the letter first.")
    if st.button("Read aloud", icon=":material/volume_up:", width="stretch", type="primary", help="Requires internet. Sends transcript to Google. Indonesian pronunciation.",
                 disabled=not st.session_state.sentence.strip()):
        if not st.session_state.sentence.strip():
            st.warning("Transcript is empty.")
        else:
            try:
                audio = io.BytesIO()
                with st.spinner("Preparing audio…"):
                    gTTS(st.session_state.sentence, lang="id", timeout=10).write_to_fp(audio)
                st.session_state.audio = audio.getvalue()
            except Exception as exc:
                st.error(f"Audio failed: {exc}")
    if st.session_state.audio:
        st.audio(st.session_state.audio, format="audio/mp3", autoplay=True)
    with st.expander("Diagnostics", icon=":material/speed:"):
        ago = result.get("ago")
        age = f"{ago:.1f}s ago" if ago is not None else "none"
        st.caption(f"Last frame {age} · {result.get('fps', 0) if active else 0:.1f} FPS · inference {result.get('ms', 0) if active else 0:.0f} ms")
        st.caption("FPS measures frames received by Python, not browser preview.")
    if mode == "BISINDO":
        with st.expander("Record sample"):
            label = st.selectbox("Target letter", list("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
            st.caption("3s preparation, 5s capture. Landmarks only. Download before recording again or switching language.")
            recording, rows = engine.diagnostic_snapshot()
            if st.button("Record 5 seconds", disabled=recording or not active):
                engine.start_diagnostic(label)
                recording, rows = True, []
            countdown = engine.diagnostic_countdown()
            if countdown > 0:
                st.info(f"Prepare pose · recording in {math.ceil(countdown)} seconds")
            else:
                st.caption(f"{'Recording' if recording else 'Ready'} · {len(rows)} samples")
            if rows and not recording:
                st.download_button("Download diagnostic CSV", pd.DataFrame(rows).to_csv(index=False),
                                   file_name=f"bisindo_{rows[0]['label']}_diagnosis.csv", mime="text/csv")


with right:
    results()
