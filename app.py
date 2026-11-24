from pathlib import Path

import streamlit as st

st.set_page_config(page_title="kata · Ruang belajar isyarat", page_icon=":material/sign_language:", layout="wide")
st.html(Path(__file__).resolve().parent / "assets/workspace.css")
for key, value in {"sentence": "", "audio": None, "engine": None, "candidate": ""}.items():
    st.session_state.setdefault(key, value)

with st.sidebar:
    st.title("kata.")
    st.caption("Ruang belajar abjad isyarat")
    st.space("medium")

page = st.navigation([
    st.Page("app_pages/isyarat.py", title="Isyarat ke teks", url_path="isyarat", icon=":material/sign_language:", default=True),
    st.Page("app_pages/grafis.py", title="Teks ke grafis", url_path="grafis", icon=":material/grid_view:"),
    st.Page("app_pages/panduan.py", title="Panduan", url_path="panduan", icon=":material/menu_book:"),
], position="sidebar")

# Halaman non-kamera melepas worker dan registrasi token sesi.
if page.title != "Isyarat ke teks" and st.session_state.engine is not None:
    from local_camera import get_frame_server

    get_frame_server().unregister(st.session_state.frame_token)
    st.session_state.engine.close()
    st.session_state.engine = None

with st.sidebar:
    st.space("large")
    st.caption("DEMO LOKAL")
    st.caption("Abjad statis SIBI & BISINDO. Bukan penerjemah tata bahasa isyarat.")

page.run()
