import streamlit as st

with st.container(key="workspace"), st.container(border=True):
    st.subheader("Help", anchor=False)
    with st.expander("Sign to text", expanded=True):
        st.markdown("1. Choose SIBI or BISINDO and turn the camera on.\n2. Keep all fingers visible in even light. Hold a static letter pose until captured.\n3. Release your hand before repeating the same letter.\n4. Use Space, Delete, and Reset to edit. Turn the camera off when finished.")
        st.write("Mirror changes preview only. Flip model input changes inference. BISINDO hand order must match training; support for both hands is not validated.")
    with st.expander("Text to graphics"):
        st.write("Spell A–Z, up to 120 characters. Press Enter to apply; spaces separate words. Browse longer text eight letters per page. SIBI and BISINDO assets are supplied by the contributor; poses and licensing have not been independently verified.")
        st.write("Static graphics do not demonstrate movement. This app recognizes static alphabet poses, not sign-language grammar or dynamic gestures. Speech input is not available.")
    with st.expander("Privacy and limitations"):
        st.write("Microphone is disabled. Preview stays in your browser; JPEG frames are sent over the Streamlit connection to the app server for inference. Images are not saved by the app. Diagnostic CSV files contain landmarks and predictions, not images.")
        st.write("Read aloud requires internet and sends transcript to Google through gTTS. Pronunciation is Indonesian. Use HTTPS for hosted access. Free hosting can sleep or limit resources; avoid sensitive content.")
        st.write("Reported evaluation accuracy: SIBI 95.92%, BISINDO 95.95%. Not guaranteed webcam accuracy. Pose, position, lighting, and training alignment affect results.")
