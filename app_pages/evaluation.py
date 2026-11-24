import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
report = json.loads((ROOT / "assets/benchmark.json").read_text(encoding="utf-8"))
analysis = json.loads((ROOT / "assets/evaluation.json").read_text(encoding="utf-8"))

with st.container(key="landing"):
    with st.container(horizontal=True, horizontal_alignment="distribute", key="evaluation-nav"):
        st.page_link("app_pages/home.py", label="Back to home", icon=":material/arrow_back:")
        st.page_link("app_pages/isyarat.py", label="Open workspace", icon=":material/arrow_outward:")
    with st.container(key="evaluation-content"):
        st.title("Why we chose SVM.", anchor=False)
        st.markdown("Three models, two alphabets. A closer look at the evidence behind sesama.")
        st.info("Offline evaluation of static alphabets, not guaranteed webcam accuracy. The model was selected on the same test split used to report these scores.")

        st.header("Compare the results", anchor=False)
        metric = st.segmented_control("Comparison metric", ["Weighted F1", "Accuracy", "Precision", "Recall"], default="Weighted F1", required=True, width="stretch")
        metric_key = {"Weighted F1": "weighted_f1", "Accuracy": "accuracy", "Precision": "precision", "Recall": "recall"}[metric]
        for dataset, column in zip(report["datasets"], st.columns(2, gap="large")):
            with column:
                st.subheader(dataset["name"], anchor=False)
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

        st.header("Why this model", anchor=False)
        st.markdown("**Weighted F1 determined the choice.** SVM (RBF) ranked first for both SIBI and BISINDO; accuracy also ranked first. Weighted F1 combines precision and recall per class, then weights by class sample count. It can hide weak results on less frequent classes.")
        st.markdown("The RBF kernel can model nonlinear boundaries in the scaled landmark features. That describes how the model works, not proof of why it won. The recorded comparison supports choosing it for these datasets—not a claim that SVM always beats tree models or runs fastest.")

        st.header("How we compared", anchor=False)
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

        st.header("Inside the SIBI evaluation", anchor=False)
        st.markdown("SVM predictions from the reconstructed notebook test split: **235 correct out of 245**. Rows show actual letters; columns show predictions. Hover over a cell for counts. No BISINDO confusion matrix is presented here.")
        matrix = analysis["sibi_confusion"]
        cells = pd.DataFrame([{"Actual": actual, "Predicted": predicted, "Count": matrix["counts"][i][j],
                               "Row share": matrix["counts"][i][j] / sum(matrix["counts"][i])}
                              for i, actual in enumerate(matrix["labels"]) for j, predicted in enumerate(matrix["labels"])])
        heatmap = alt.Chart(cells).mark_rect(stroke="#f5f7f6", strokeWidth=.5).encode(
            x=alt.X("Predicted:O", sort=matrix["labels"], axis=alt.Axis(labelAngle=0, labelFontSize=8, labelOverlap=False)),
            y=alt.Y("Actual:O", sort=matrix["labels"], axis=alt.Axis(labelFontSize=8, labelOverlap=False)),
            color=alt.Color("Count:Q", scale=alt.Scale(domain=[0, int(cells["Count"].max())], range=["#eef2f5", "#526f8c"]), legend=None),
            tooltip=["Actual:O", "Predicted:O", alt.Tooltip("Count:Q", format="d"), alt.Tooltip("Row share:Q", format=".1%")],
        )
        st.altair_chart(heatmap.properties(height=400), width="stretch", key="confusion-chart")
        with st.expander("Supporting analysis"):
            st.subheader("Random Forest feature importance", anchor=False)
            st.markdown("SIBI, top 10 features. Recomputed with notebook settings; accuracy and weighted F1 match the saved RF scores to six decimals. This is **not SVM feature importance**, nor a causal explanation of its lead.")
            importance = pd.DataFrame(analysis["rf_importance"]["features"])
            st.altair_chart(alt.Chart(importance).mark_bar(color="#b3a4cb", cornerRadiusEnd=4).encode(
                x=alt.X("importance:Q", title="Feature importance", scale=alt.Scale(zero=True)),
                y=alt.Y("feature:N", sort="-x", title=None),
                tooltip=[alt.Tooltip("feature:N", title="Feature"), alt.Tooltip("importance:Q", title="Importance", format=".4f")],
            ).properties(height=300), width="stretch", key="importance-chart")
            st.subheader("Samples per letter", anchor=False)
            st.markdown("Source CSV rows **before deduplication**, matching the EDA stage. Dataset context, not test-set class counts or model performance.")
            counts = pd.DataFrame([{"Dataset": d["dataset"], "Letter": letter, "Samples": count}
                                   for d in analysis["class_distributions"] for letter, count in d["counts"].items()])
            for name, column in zip(["SIBI", "BISINDO"], st.columns(2, gap="large")):
                with column:
                    st.markdown(f"**{name}**")
                    st.altair_chart(alt.Chart(counts[counts["Dataset"] == name]).mark_bar(color="#9cb8cf" if name == "SIBI" else "#b3a4cb").encode(
                        x=alt.X("Letter:O", axis=alt.Axis(labelAngle=0, labelFontSize=8)),
                        y=alt.Y("Samples:Q", scale=alt.Scale(zero=True)), tooltip=["Letter:O", "Samples:Q"],
                    ).properties(height=220), width="stretch")

        st.header("Read the limits", anchor=False)
        st.markdown("""
- **Selection used the test split.** No separate final holdout or cross-validation is reported in this comparison; performance after selection can be optimistic.
- **No signer-independent result is reported.** A row-level random split does not establish generalization to unseen people or capture sessions.
- **No speed benchmark or uncertainty interval is reported.** These scores do not prove a statistically significant lead or lower latency.
- **Webcam conditions differ.** Lighting, pose, orientation, and connection quality affect live results. Static alphabets only, not moving gestures or full sign-language translation.
""")
        st.header("Sources", anchor=False)
        st.markdown("""
- `notebooks/03_pemodelan_dan_evaluasi.ipynb`: saved model scores, split procedure, settings, SVM selection, confusion matrix, and Random Forest feature importance.
- `notebooks/02_eda_dan_preprocessing.ipynb` and `reports/figures/`: supporting dataset analysis and original figures.
- `assets/benchmark.json`: six-decimal transcription of saved comparison scores; displayed percentages rounded to two decimals.
- `assets/evaluation.json`: numeric chart export from local CSVs and trusted model artifacts. `scripts/export_evaluation.py` reconstructs the split, verifies SVM and refitted RF scores, and records source hashes. No fitting or inference runs when this page opens.
""")
        with st.container(key="evaluation-back"):
            st.page_link("app_pages/home.py", label="Back to home", icon=":material/arrow_back:")
