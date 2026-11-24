from pathlib import Path
import base64
import html
import math

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

with st.container(key="workspace"):
    left, right = st.columns([1, 3], gap="small")
    with left, st.container(border=True, key="visual-input"):
        st.subheader("Text to graphics")
        mode = st.segmented_control("Sign language", ["BISINDO", "SIBI"], default="BISINDO", required=True, key="visual_mode", persist_state="session", width="stretch")
        text = st.text_input("Text to spell", max_chars=120, placeholder="Type a word…", key="visual_text", persist_state="session", help="Press Enter. A–Z only; spaces separate words. Up to 120 characters.")
        st.button("Clear", icon=":material/backspace:", on_click=lambda: st.session_state.update(visual_text=""))
    with right, st.container(border=True, key="visual-output"):
        st.subheader("Letter graphics")
        if not text.strip():
            st.space("large")
            st.markdown(":material/sign_language: **Your words, in signs**")
            st.caption("Type a word to begin.")
            st.space("large")
        letters = [(number, char) for number, word in enumerate(text.upper().split(), 1) for char in word]
        # ponytail: eight letters per page keep gallery bounded; use virtual grid for longer documents.
        pages = max(1, math.ceil(len(letters) / 8))
        page = st.pagination(pages, key=f"graphics-page-{mode}-{text}") - 1 if pages > 1 else 0
        tiles = []
        for number, char in letters[page * 8:(page + 1) * 8]:
            path = next((p for ext in ("png", "jpeg", "jpg") if (p := ROOT / "assets" / mode / f"{char}.{ext}").is_file()), None) if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else None
            if path:
                mime = "image/png" if path.suffix == ".png" else "image/jpeg"
                source = base64.b64encode(path.read_bytes()).decode("ascii")
                image = f'<img src="data:{mime};base64,{source}" alt="{mode} letter {char}">'
            else:
                message = "Asset unavailable" if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else "Unsupported character"
                image = f'<div class="letter-missing">{html.escape(char)}<br>{message}</div>'
            tiles.append(f'<figure>{image}<figcaption>{mode} · {html.escape(char)} · Word {number}</figcaption></figure>')
        if tiles:
            st.html('<div class="letter-grid">' + "".join(tiles) + '</div>')
