import streamlit as st

SECTIONS = [("how-it-works", "How it works"), ("benchmark", "Benchmark"),
            ("benefits", "Benefits"), ("faq", "FAQ")]
links = ''.join(f'<a href="#{anchor}" target="_self">{label}</a>' for anchor, label in SECTIONS)

with st.container(key="landing"):
    st.html(
        '<nav class="landing-nav" aria-label="Main navigation">'
        '<a class="landing-brand" href="/" target="_self" aria-label="sesama home">sesama</a>'
        f'<div class="desktop-links">{links}</div>'
        '<a class="nav-launch" href="/sign-to-text" target="_self">Open workspace <span aria-hidden="true">↗</span></a>'
        f'<details class="mobile-nav"><summary>Menu</summary><div>{links}</div></details>'
        '</nav>'
    )
    with st.container(key="landing-hero"):
        st.title("Every letter. A little closer.")
        st.markdown("Connect through SIBI & BISINDO.")
        with st.container(horizontal=True, horizontal_alignment="center", key="hero-actions"):
            if st.button("Try sign to text", type="primary", icon=":material/arrow_forward:"):
                st.switch_page("app_pages/isyarat.py")

    # ponytail: section anchors only; replace placeholders when section content is approved.
    for anchor, label in SECTIONS:
        st.html(f'<section class="landing-placeholder" id="{anchor}" aria-label="{label}"><h2>{label}</h2><p>Coming soon.</p></section>')
