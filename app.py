from pathlib import Path

import streamlit as st

st.set_page_config(page_title="kata · Ruang belajar isyarat", page_icon=":material/sign_language:", layout="wide")
st.html(Path(__file__).resolve().parent / "assets/workspace.css")
for key, value in {"sentence": "", "audio": None, "engine": None, "candidate": ""}.items():
    st.session_state.setdefault(key, value)

pages = [
    st.Page("app_pages/isyarat.py", title="Isyarat ke teks", url_path="isyarat", icon=":material/sign_language:", default=True),
    st.Page("app_pages/grafis.py", title="Teks ke grafis", url_path="grafis", icon=":material/grid_view:"),
    st.Page("app_pages/panduan.py", title="Panduan", url_path="panduan", icon=":material/menu_book:"),
]
page = st.navigation(pages, position="hidden")
with st.sidebar:
    expanded = st.session_state.get("nav_expanded", False)
    if st.button("Ringkas navigasi" if expanded else "Perluas navigasi", icon=":material/menu:", key="nav-toggle", help="Tampilkan atau sembunyikan nama halaman", width="stretch"):
        st.session_state.nav_expanded = not expanded
        st.rerun()
    st.html(f'<style>[data-testid="stSidebar"] {{width: {"220" if expanded else "88"}px !important; min-width: {"220" if expanded else "88"}px !important; max-width: {"220" if expanded else "88"}px !important;}}</style>')
    with st.container(key="nav-expanded" if expanded else "nav-compact"):
        for item in pages:
            with st.container(key=f"nav-{'active' if item.title == page.title else item.url_path}"):
                st.page_link(item, label=item.title, icon=item.icon, help=item.title)

# Halaman non-kamera melepas worker dan registrasi token sesi.
if page.title != "Isyarat ke teks" and st.session_state.engine is not None:
    from local_camera import get_frame_server

    get_frame_server().unregister(st.session_state.frame_token)
    st.session_state.engine.close()
    st.session_state.engine = None

page.run()
