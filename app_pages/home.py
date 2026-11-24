import base64
from pathlib import Path

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

    hand_image = base64.b64encode((Path(__file__).resolve().parents[1] / "assets/SIBI/H.jpeg").read_bytes()).decode("ascii")
    paused = st.session_state.get("tutorials_paused", False)
    st.html(f'''
        <section class="how-section{' motion-paused' if paused else ''}" id="how-it-works" aria-labelledby="how-title">
          <div class="how-heading"><h2 id="how-title">From signs to words.</h2><p>Three steps. Your own pace.</p></div>
          <ol class="how-steps">
            <li><span class="step-number" aria-hidden="true">01</span>
              <div class="alphabet-motion">
                <div class="motion-stage" role="img" aria-label="Illustration: cursor switches the sign language selection between SIBI and BISINDO.">
                  <div class="motion-settings" aria-hidden="true"><span class="motion-label">Sign language</span>
                    <div class="motion-options"><span class="motion-selection"></span><span>SIBI</span><span>BISINDO</span></div>
                  </div>
                  <span class="motion-cursor" aria-hidden="true"></span>
                </div>
              </div>
              <h3>Choose your alphabet.</h3><p>Open the workspace and select SIBI or BISINDO.</p></li>
            <li><span class="step-number" aria-hidden="true">02</span>
              <div class="camera-motion motion-stage" role="img" aria-label="Illustration, not a live camera: cursor clicks Start, then a sample SIBI hand pose appears with a reminder to hold steady.">
                <span class="motion-example" aria-hidden="true">Illustration</span>
                <div class="camera-demo" aria-hidden="true">
                  <span class="demo-start">START</span>
                  <div class="demo-pose"><img src="data:image/jpeg;base64,{hand_image}" alt=""><span class="pose-corner corner-left"></span><span class="pose-corner corner-right"></span></div>
                  <span class="demo-hold">Hold steady</span>
                </div>
                <span class="motion-cursor" aria-hidden="true"></span>
              </div>
              <h3>Make a sign.</h3><p>Start the camera. Keep your hand sign steady and in view.</p></li>
            <li><span class="step-number" aria-hidden="true">03</span><h3>Build your words.</h3><p>Check each recognized letter, then add spaces or edit your text.</p></li>
          </ol>
          <div class="how-bottom"><p>Static letters only. Not full sign-language translation.</p><a href="/text-to-graphics" target="_self">Prefer to explore letters? <span>Try text to graphics ↗</span></a></div>
        </section>
    ''')
    st.button("Resume animations" if paused else "Pause animations", icon=":material/play_arrow:" if paused else ":material/pause:",
              key="tutorial-motion", on_click=lambda: st.session_state.update(tutorials_paused=not paused))

    # ponytail: remaining anchors only; replace placeholders when section content is approved.
    for anchor, label in SECTIONS[1:]:
        st.html(f'<section class="landing-placeholder" id="{anchor}" aria-label="{label}"><h2>{label}</h2><p>Coming soon.</p></section>')
