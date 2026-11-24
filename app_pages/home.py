import base64
import json
from datetime import date
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
    camera_icon = base64.b64encode(b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="1.7"><rect x="3" y="6" width="12" height="12" rx="3"/><path d="m15 10 6-3v10l-6-3"/></svg>').decode("ascii")
    st.html(f'''
        <section class="how-section" id="how-it-works" aria-labelledby="how-title">
          <div class="how-heading"><h2 id="how-title">From signs to words.</h2><p>Three steps. Your own pace.</p></div>
          <ol class="how-steps">
            <li><span class="step-number" aria-hidden="true">01</span>
              <div class="alphabet-motion">
                <div class="motion-stage" role="img" aria-label="Illustration: cursor switches the sign language selection between SIBI and BISINDO.">
                  <div class="motion-settings" aria-hidden="true">
                    <div class="motion-options"><span class="motion-selection"></span><span>SIBI</span><span>BISINDO</span></div>
                  </div>
                  <span class="motion-cursor" aria-hidden="true"></span>
                </div>
              </div>
              <h3>Choose your alphabet.</h3><p>Open the workspace and select SIBI or BISINDO.</p></li>
            <li><span class="step-number" aria-hidden="true">02</span>
              <div class="camera-motion motion-stage" role="img" aria-label="Illustration, not a live camera: cursor turns the camera icon from off to on, then a sample SIBI hand pose appears with a reminder to hold steady.">
                <div class="camera-demo" aria-hidden="true">
                  <div class="demo-pose"><img src="data:image/jpeg;base64,{hand_image}" alt=""><span class="pose-corner corner-left"></span><span class="pose-corner corner-right"></span></div>
                  <span class="demo-hold">Hold steady</span>
                </div>
                <span class="demo-camera" aria-hidden="true"><img src="data:image/svg+xml;base64,{camera_icon}" alt=""><span class="demo-camera-slash"></span></span>
                <span class="motion-cursor" aria-hidden="true"></span>
              </div>
              <h3>Make a sign.</h3><p>Start the camera. Keep your hand sign steady and in view.</p></li>
            <li><span class="step-number" aria-hidden="true">03</span>
              <div class="text-motion motion-stage" role="img" aria-label="Illustration: H and I appear in the transcript. The cursor adds a space, then deletes that space.">
                <div class="text-demo" aria-hidden="true">
                  <div class="demo-transcript"><span class="demo-letter-h">H</span><span class="demo-letter-i">I</span><span class="demo-space"></span><span class="demo-caret"></span></div>
                  <div class="demo-edit"><span class="demo-space-key">Space</span><span class="demo-delete-key">Delete</span></div>
                </div>
                <span class="motion-cursor" aria-hidden="true"></span>
              </div>
              <h3>Build your words.</h3><p>Check each recognized letter, then add spaces or edit your text.</p></li>
          </ol>
          <div class="how-bottom"><p>Static letters only. Not full sign-language translation.</p><a href="/text-to-graphics" target="_self">Prefer to explore letters? <span>Try text to graphics ↗</span></a></div>
        </section>
    ''')

    benchmark = json.loads((Path(__file__).resolve().parents[1] / "assets/benchmark.json").read_text(encoding="utf-8"))
    tables = []
    for dataset in benchmark["datasets"]:
        winner = max(dataset["models"], key=lambda model: model["weighted_f1"])
        rows = []
        for model in dataset["models"]:
            selected = ' class="benchmark-selected"' if model is winner else ''
            tag = '<span class="selected-tag">Selected</span>' if model is winner else ''
            rows.append(f'<tr{selected}><th scope="row">{model["name"]}{tag}</th><td>{model["accuracy"]:.2%}</td><td>{model["weighted_f1"]:.2%}</td></tr>')
        tables.append(f'<div class="benchmark-dataset"><table><caption>{dataset["name"]}</caption><thead><tr><th scope="col">Model</th><th scope="col">Accuracy</th><th scope="col">F1 <span class="metric-weight">(weighted)</span></th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
    st.html('''
        <section class="benchmark-section" id="benchmark" aria-labelledby="benchmark-title">
          <div class="benchmark-heading"><h2 id="benchmark-title">Why SVM? The results.</h2><p>Three models. The same split. One clear choice.</p></div>
          <div class="benchmark-tables">''' + ''.join(tables) + '''</div>
          <div class="benchmark-verdict"><h3>Highest F1. Both alphabets.</h3><p>SVM with an RBF kernel scored the highest weighted F1 on both datasets. That is why it powers recognition in sesama.</p></div>
          <a class="evaluation-link" href="/model-evaluation" target="_self">Explore model evaluation <span aria-hidden="true">↗</span></a>
        </section>
    ''')

    st.html('''
        <section class="benefits-section" id="benefits" aria-labelledby="benefits-title">
          <div class="benefits-heading"><h2 id="benefits-title">Small gestures.<br>More possibilities.</h2><p>A little help, letter by letter.</p></div>
          <ul class="benefits-list">
            <li><h3>Two alphabets. One place.</h3><p>Explore static SIBI and BISINDO letters in the same workspace.</p></li>
            <li><h3>Your words. Your control.</h3><p>Review recognized letters, add spaces, and edit your text before sharing.</p></li>
            <li><h3>Text, with a voice.</h3><p>Let your finished text be heard with online text-to-speech.</p></li>
          </ul>
        </section>
    ''')

    with st.container(key="landing-faq"):
        st.html('<header id="faq" class="faq-heading"><h2>Questions? Start here.</h2></header>')
        for question, answer in [
            ("Does sesama translate full sign language?",
             "No. sesama recognizes static alphabet poses in SIBI and BISINDO. It does not interpret moving gestures, facial expressions, or sign-language grammar."),
            ("What do I need to get started?",
             "A camera and a browser with camera permission. Open the workspace, choose SIBI or BISINDO, and turn on the camera. Keep your hands fully in view with even lighting. No microphone is needed."),
            ("What if a letter is recognized incorrectly?",
             "Check the selected alphabet, keep your pose steady, and adjust lighting or framing. Review the transcript and edit any incorrect letters; recognition is not always correct."),
            ("How accurate is it, and why SVM?",
             "SVM achieved 95.92% accuracy on the SIBI test split and 95.95% on BISINDO. It had the highest weighted F1 among the three compared models. These offline scores do not guarantee webcam accuracy. Explore the full comparison and its limits below."),
            ("Where do my camera frames go?",
             "Frames are sent to the app server for recognition, not processed only in your browser. The app does not save camera images. Turn off the camera to stop capture."),
            ("Do I need an internet connection?",
             "The hosted app requires internet. Read aloud also requires internet and sends your transcript to Google through gTTS for Indonesian pronunciation. Camera recognition does not use your microphone."),
        ]:
            with st.expander(question):
                st.markdown(answer)
                if question == "How accurate is it, and why SVM?":
                    st.page_link("app_pages/evaluation.py", label="Model evaluation", icon=":material/arrow_outward:")

    st.html(f'''
        <footer class="landing-footer" role="contentinfo" aria-label="Site footer">
          <div class="footer-columns">
            <div class="footer-about"><a class="footer-brand" href="/" target="_self" aria-label="sesama home">sesama</a><p>Bringing static SIBI &amp; BISINDO letters closer, one sign at a time.</p></div>
            <div class="footer-institution"><h2>Institution</h2><p>IPB University<br>Machine Learning project<br>Bogor, West Java, Indonesia</p></div>
            <nav class="footer-explore" aria-label="Footer navigation"><h2>Explore</h2><div class="footer-links">
              <a href="/sign-to-text" target="_self">Open workspace</a><a href="#how-it-works" target="_self">How it works</a>
              <a href="/model-evaluation" target="_self">Model evaluation</a><a href="#benefits" target="_self">Benefits</a>
              <a href="/text-to-graphics" target="_self">Text to graphics</a><a href="#faq" target="_self">FAQ</a>
            </div></nav>
          </div>
          <div class="footer-bottom"><p>© {date.today().year} sesama</p><p>A Machine Learning course project.</p></div>
        </footer>
    ''')
