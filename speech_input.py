"""Browser speech recognition; no audio recording stored by the app."""
from pathlib import Path

import streamlit as st

speech_input = st.components.v2.component(
    "speech_input",
    html='<div class="speech-row"><button type="button" aria-label="Turn microphone on" aria-pressed="false"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"/><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3m-4 0h8"/></svg></button><span role="status" aria-live="polite">Voice input</span></div>',
    css='''
.speech-row {display:flex;align-items:center;gap:12px;min-width:0;}
button {flex:0 0 44px;width:44px;height:44px;display:grid;place-items:center;border:1px solid #dce1dd;border-radius:50%;background:#f5f7f6;color:#242522;cursor:pointer;font-size:22px;}
button[aria-pressed="true"] {background:#242522;color:white;}
button:focus-visible {outline:2px solid #596347;outline-offset:3px;}
button:disabled {opacity:.5;cursor:not-allowed;}
span {min-width:0;font:14px/1.5 sans-serif;color:#5d655f;}
''',
    js=(Path(__file__).parent / "assets/speech_input.js").read_text(encoding="utf-8"),
)


def apply_transcript(value):
    if isinstance(value, str) and len(value) <= 120:
        st.session_state.visual_text = " ".join(value.split())
