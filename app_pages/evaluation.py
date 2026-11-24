import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / "assets/benchmark.json").read_text(encoding="utf-8"))

with st.container(key="landing"):
    with st.container(horizontal=True, horizontal_alignment="distribute", key="evaluation-nav"):
        st.page_link("app_pages/home.py", label="Back to home", icon=":material/arrow_back:")
        st.page_link("app_pages/isyarat.py", label="Open workspace", icon=":material/arrow_outward:")
    with st.container(key="evaluation-content"):
        st.title("Why we chose SVM.")
        st.markdown("Three models, two alphabets. A closer look at the evidence behind sesama.")
        st.info("Offline evaluation of static alphabets, not guaranteed webcam accuracy. The model was selected on the same test split used to report these scores.")

        st.header("Compare the results")
        metric = st.segmented_control("Comparison metric", ["Weighted F1", "Accuracy", "Precision", "Recall"], default="Weighted F1", required=True, width="stretch")
        metric_key = {"Weighted F1": "weighted_f1", "Accuracy": "accuracy", "Precision": "precision", "Recall": "recall"}[metric]
        for dataset, column in zip(report["datasets"], st.columns(2, gap="large")):
            with column:
                st.subheader(dataset["name"])
                frame = pd.DataFrame(dataset["models"])
                # Zero baseline preserves honest visual comparisons between close scores.
                bars = alt.Chart(frame).mark_bar(cornerRadiusEnd=4).encode(
                    x=alt.X(f"{metric_key}:Q", title=metric, scale=alt.Scale(domain=[0, 1]), axis=alt.Axis(format=".0%")),
                    y=alt.Y("name:N", title=None, sort=frame["name"].tolist()),
                    color=alt.Color("name:N", scale=alt.Scale(domain=frame["name"].tolist(), range=["#526546", "#9cb8cf", "#b3a4cb"]), legend=None),
                    tooltip=[alt.Tooltip("name:N", title="Model"), alt.Tooltip(f"{metric_key}:Q", title=metric, format=".2%")],
                )
                labels = bars.mark_text(align="right", dx=-8).encode(text=alt.Text(f"{metric_key}:Q", format=".2%"), color=alt.condition(alt.datum.name == "SVM (RBF)", alt.value("#fff"), alt.value("#20211f")))
                st.altair_chart((bars + labels).properties(height=190), width="stretch")
                st.dataframe(frame.rename(columns={"name": "Model", "accuracy": "Accuracy", "precision": "Precision", "recall": "Recall", "weighted_f1": "Weighted F1"}).set_index("Model").map(lambda value: f"{value:.2%}"), width="stretch")
                winner = max(dataset["models"], key=lambda model: model["weighted_f1"])
                runner_up = sorted(dataset["models"], key=lambda model: model["weighted_f1"], reverse=True)[1]
                gap = (winner["weighted_f1"] - runner_up["weighted_f1"]) * 100
                st.markdown(f'**SVM leads weighted F1 by {gap:.2f} percentage points** over {runner_up["name"]} on this split.')

        st.header("Why this model")
        st.markdown("**Weighted F1 determined the choice.** SVM (RBF) ranked first for both SIBI and BISINDO; accuracy also ranked first. Weighted F1 combines precision and recall per class, then weights by class sample count. It can hide weak results on less frequent classes.")
        st.markdown("The RBF kernel can model nonlinear boundaries in the scaled landmark features. That describes how the model works, not proof of why it won. The recorded comparison supports choosing it for these datasets—not a claim that SVM always beats tree models or runs fastest.")

        st.header("How we compared")
        st.markdown("Exact duplicate rows removed. Labels encoded, then split **80% train / 20% test**, stratified by letter with `random_state=42`. `StandardScaler` fitted on training data only. All three models used the same scaled split within each alphabet.")
        st.dataframe(pd.DataFrame([{"Dataset": d["name"], "Train samples": d["train_samples"], "Test samples": d["test_samples"], "Landmark features": d["features"]} for d in report["datasets"]]), hide_index=True, width="stretch")
        st.markdown("""
| Model | Recorded settings |
|---|---|
| SVM | RBF kernel, `C=10`, `gamma='scale'`, `probability=True` |
| Random Forest | `n_estimators=100`, `max_depth=15` |
| XGBoost | `n_estimators=100`, `learning_rate=0.1`, `max_depth=6`, `eval_metric='mlogloss'` |

All three used `random_state=42`. These are the compared configurations, not an exhaustive search of each model family.
""")

        st.header("Inside the SIBI evaluation")
        st.markdown("Original figures from the project reports. The available training report contains a SIBI confusion matrix; no BISINDO confusion matrix is supplied here.")
        st.image(str(ROOT / "reports/figures/confusion_matrix_sibi.png"), caption="SVM (RBF), SIBI test split. Rows: actual letters. Columns: predicted letters. Counts, not percentages.", width="stretch")
        with st.expander("Supporting analysis"):
            st.image(str(ROOT / "reports/figures/feature_importance_sibi.png"), caption="Random Forest feature importance, SIBI. This explains that tree model's feature use, not SVM feature importance or a causal explanation of SVM's lead.", width="stretch")
            st.image(str(ROOT / "reports/figures/distribusi_kelas_abjad.png"), caption="Class distribution from EDA. This is dataset context, not a ranking of model performance or necessarily the post-deduplication test distribution.", width="stretch")

        st.header("Read the limits")
        st.markdown("""
- **Selection used the test split.** No separate final holdout or cross-validation is reported in this comparison; performance after selection can be optimistic.
- **No signer-independent result is reported.** A row-level random split does not establish generalization to unseen people or capture sessions.
- **No speed benchmark or uncertainty interval is reported.** These scores do not prove a statistically significant lead or lower latency.
- **Webcam conditions differ.** Lighting, pose, orientation, and connection quality affect live results. Static alphabets only, not moving gestures or full sign-language translation.
""")
        st.header("Sources")
        st.markdown("""
- `notebooks/03_pemodelan_dan_evaluasi.ipynb`: saved model scores, split procedure, settings, SVM selection, confusion matrix, and Random Forest feature importance.
- `notebooks/02_eda_dan_preprocessing.ipynb` and `reports/figures/`: supporting dataset analysis and original figures.
- `assets/benchmark.json`: six-decimal transcription of saved comparison scores. Charts use these values; no retraining runs when this page opens. Displayed percentages rounded to two decimals.
""")
        st.page_link("app_pages/home.py", label="Back to home", icon=":material/arrow_back:")
