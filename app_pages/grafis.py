from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

with st.container(key="workspace"):
    left, right = st.columns([1, 3], gap="small")
    with left, st.container(border=True, key="visual-input"):
        st.subheader("Text to graphics")
        mode = st.segmented_control("Sign language", ["BISINDO", "SIBI"], default="BISINDO", required=True, key="visual_mode", persist_state="session")
        text = st.text_area("Text to spell", max_chars=120, placeholder="Type a word…", key="visual_text", height=180, persist_state="session", help="A–Z only. Spaces separate words. Up to 120 characters.")
        st.button("Clear", icon=":material/backspace:", on_click=lambda: st.session_state.update(visual_text=""))
    with right, st.container(border=True, key="visual-output", height=570):
        st.subheader("Letter graphics")
        if not text.strip():
            st.space("large")
            st.markdown(":material/sign_language: **Your words, in signs**")
            st.caption("Type a word to begin.")
            st.space("large")
        for number, word in enumerate(text.upper().split(), 1):
            st.caption(f"WORD {number} · {word}")
            for start in range(0, len(word), 4):
                columns = st.columns(4)
                for column, char in zip(columns, word[start:start + 4]):
                    with column:
                        path = ROOT / "assets/BISINDO" / (f"{char}.jpeg" if char == "I" else f"{char}.png") if mode == "BISINDO" and char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else None
                        if path and path.is_file():
                            st.image(str(path), caption=f"{mode} · {char}", width="stretch")
                        else:
                            with st.container(border=True):
                                st.subheader(char)
                                st.caption("Asset unavailable" if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else "Unsupported character")
