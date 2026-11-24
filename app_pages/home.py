from pathlib import Path
import base64

import streamlit as st

with st.container(key="landing"):
    with st.container(key="landing-nav", horizontal=True, vertical_alignment="center"):
        st.markdown("**sesama**")
        with st.container(horizontal=True, horizontal_alignment="right", vertical_alignment="center"):
            st.page_link("app_pages/grafis.py", label="Text to graphics")
            st.page_link("app_pages/panduan.py", label="Help")
            with st.container(key="nav-launch"):
                st.page_link("app_pages/isyarat.py", label="Open workspace", icon=":material/arrow_outward:")

    with st.container(key="landing-hero"):
        copy, visual = st.columns([1.15, 1], gap="large", vertical_alignment="center")
        with copy:
            st.html('<p class="hero-eyebrow">A LITTLE SIGN. A NEW CONNECTION.</p>')
            st.title("Every letter. A little closer.")
            st.markdown("Explore Indonesian fingerspelling with **SIBI and BISINDO**. Recognize static hand signs through your camera, or turn your words into letter graphics.")
            with st.container(horizontal=True, key="hero-actions"):
                if st.button("Try sign to text", type="primary", icon=":material/arrow_forward:"):
                    st.switch_page("app_pages/isyarat.py")
                if st.button("Explore letter graphics", icon=":material/grid_view:"):
                    st.switch_page("app_pages/grafis.py")
            st.caption("Free to try · No account needed · Camera starts only when you choose")
        with visual:
            root = Path(__file__).resolve().parents[1]
            tiles = []
            for letter in "HI":
                image = base64.b64encode((root / "assets" / "SIBI" / f"{letter}.jpeg").read_bytes()).decode("ascii")
                tiles.append(f'<figure><img src="data:image/jpeg;base64,{image}" alt="SIBI letter {letter}"><figcaption>{letter}</figcaption></figure>')
            st.html('<div class="hero-demo"><div class="demo-top"><span>SMALL SIGNS, SHARED MEANING</span><span class="demo-badge">SIBI</span></div><div class="demo-letters">' + ''.join(tiles) + '</div><div class="demo-bottom"><span>A hello starts here.</span><span class="demo-word">Hi.</span></div></div>')
    st.html('<p class="landing-note">Built for learning static alphabets, not translating full sign language or moving gestures.</p>')
