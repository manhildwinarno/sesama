import base64
import json
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
    metrics = []
    for dataset in benchmark["datasets"]:
        winner = max(dataset["models"], key=lambda model: model["weighted_f1"])
        rows = []
        for model in dataset["models"]:
            selected = ' class="benchmark-selected"' if model is winner else ''
            tag = '<span class="selected-tag">Selected</span>' if model is winner else ''
            rows.append(f'<tr{selected}><th scope="row">{model["name"]}{tag}</th><td>{model["accuracy"]:.2%}</td><td>{model["weighted_f1"]:.2%}</td></tr>')
        tables.append(f'<div class="benchmark-dataset"><table><caption>{dataset["name"]}</caption><thead><tr><th scope="col">Model</th><th scope="col">Accuracy</th><th scope="col">F1 <span class="metric-weight">(weighted)</span></th></tr></thead><tbody>{"".join(rows)}</tbody></table></div>')
        metrics.append(f'<li><strong>{dataset["name"]}</strong>: {dataset["train_samples"]:,} train / {dataset["test_samples"]:,} test samples, {dataset["features"]} landmark features.</li>')
    st.html('''
        <section class="benchmark-section" id="benchmark" aria-labelledby="benchmark-title">
          <div class="benchmark-heading"><h2 id="benchmark-title">Why SVM? The results.</h2><p>Three models. The same split. One clear choice.</p></div>
          <div class="benchmark-tables">''' + ''.join(tables) + '''</div>
          <div class="benchmark-verdict"><h3>Highest F1. Both alphabets.</h3><p>SVM with an RBF kernel scored the highest weighted F1 on both datasets. That is why it powers recognition in sesama.</p></div>
          <p class="benchmark-caveat">Offline test results, not guaranteed webcam accuracy.</p>
          <details class="benchmark-method"><summary>Evaluation details</summary>
            <div class="method-content"><h3>How we compared</h3>
              <p>Exact duplicate rows removed. Stratified 80/20 split, random_state=42. StandardScaler fitted on training data only; all three models used the same scaled train/test data for each alphabet.</p>
              <ul>''' + ''.join(metrics) + '''</ul>
              <p>Accuracy measures correct predictions. Weighted F1 balances precision and recall per class, weighted by class sample count; it can hide weaker results on less frequent classes.</p>
              <h3>Model settings</h3>
              <ul><li>SVM: RBF kernel, C=10, gamma=scale, probability=True.</li><li>Random Forest: 100 trees, max_depth=15.</li><li>XGBoost: 100 estimators, learning_rate=0.1, max_depth=6.</li></ul>
              <h3>What these scores do not prove</h3>
              <p>The notebook selected the model using this same test split. No separate final holdout, cross-validation, signer-independent evaluation, or inference-speed comparison is reported here. These results do not establish that SVM is always best or fastest.</p>
              <p>Live results also depend on lighting, pose, camera orientation, and connection quality. Static alphabets only, not moving gestures or full sign-language translation.</p>
              <p class="benchmark-source">Source: training notebook 03_pemodelan_dan_evaluasi.ipynb, saved evaluation outputs. Percentages rounded to two decimals.</p>
            </div>
          </details>
        </section>
    ''')

    # ponytail: remaining anchors only; replace placeholders when section content is approved.
    for anchor, label in SECTIONS[2:]:
        st.html(f'<section class="landing-placeholder" id="{anchor}" aria-label="{label}"><h2>{label}</h2><p>Coming soon.</p></section>')
