import base64

import streamlit as st

_play = st.components.v2.component(
    "speech_playback",
    html='<audio></audio><span role="status"></span>',
    js="""
export default function({parentElement, data}) {
  const audio = parentElement.querySelector('audio');
  if (audio.dataset.request === String(data.request)) return;
  audio.dataset.request = String(data.request);
  parentElement.querySelector('[role="status"]').textContent = '';
  audio.src = 'data:audio/mpeg;base64,' + data.audio;
  audio.play().catch(() => {
    parentElement.querySelector('[role="status"]').textContent =
      'Playback blocked. Allow sound in browser settings, then press Read aloud again.';
  });
}
""",
)


def play_speech(audio, request):
    _play(key="speech", data={"audio": base64.b64encode(audio).decode("ascii"), "request": request})
