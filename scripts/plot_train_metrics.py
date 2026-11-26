"""Evaluate saved SVMs without refitting. Run: python scripts/plot_train_metrics.py."""
import json
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]


def main():
    benchmark = json.loads((ROOT / "assets/benchmark.json").read_text(encoding="utf-8"))
    rows = []
    for mode, source, recorded in zip(
        ("sibi", "bisindo"),
        ("data/processed/sibi_landmarks.csv", "data/raw/BISINDO/Alphabet/landmarks_train.csv"),
        benchmark["datasets"],
    ):
        frame = pd.read_csv(ROOT / source).drop_duplicates().reset_index(drop=True)
        if pd.api.types.is_numeric_dtype(frame["label"]):
            frame["label"] = frame["label"].map({i: chr(65 + i) for i in range(26)})
        # Trusted local project artifacts only.
        model, scaler, encoder = [joblib.load(ROOT / "models" / f"{name}_{mode}.joblib")
                                  for name in ("best_model", "scaler", "le")]
        labels = encoder.transform(frame["label"])
        train, test, y_train, y_test = train_test_split(
            frame.drop(columns="label"), labels, test_size=.2, random_state=42, stratify=labels)
        assert (len(train), len(test)) == (recorded["train_samples"], recorded["test_samples"])
        assert np.allclose(scaler.mean_, train.mean(axis=0)), "Training split does not match saved scaler"
        for split, features, actual in (("Train", train, y_train), ("Test", test, y_test)):
            predicted = model.predict(scaler.transform(features))
            precision, recall, f1, _ = precision_recall_fscore_support(
                actual, predicted, average="weighted", zero_division=0)
            accuracy = accuracy_score(actual, predicted)
            if split == "Test":
                assert round(accuracy, 6) == recorded["models"][0]["accuracy"]
                assert round(f1, 6) == recorded["models"][0]["weighted_f1"]
            rows.append(dict(dataset=mode.upper(), split=split, samples=len(actual),
                             accuracy=accuracy, precision=precision, recall=recall, weighted_f1=f1))

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 12})
    fig, axes = plt.subplots(1, 2, figsize=(16, 8), facecolor="white")
    metrics = ["accuracy", "precision", "recall", "weighted_f1"]
    for ax, dataset in zip(axes, ("SIBI", "BISINDO")):
        selected = [row for row in rows if row["dataset"] == dataset]
        x = np.arange(4)
        for offset, row, color in zip((-.19, .19), selected, ("#37474f", "#78a8c4")):
            bars = ax.bar(x + offset, [row[key] * 100 for key in metrics], .36,
                          label=f'{row["split"]} (n={row["samples"]:,})', color=color)
            ax.bar_label(bars, fmt="%.2f%%", fontsize=11, padding=5)
        ax.set(title=dataset, ylim=(0, 108), ylabel="Score (%)", xticks=x,
               xticklabels=["Accuracy", "Precision\nweighted", "Recall\nweighted", "F1\nweighted"])
        ax.set_yticks(range(0, 101, 20))
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", alpha=.15)
        ax.set_axisbelow(True)
        ax.legend(loc="lower left")
    fig.suptitle("Evaluasi SVM (RBF): Train dan Test", fontsize=24, fontweight="bold", y=.96)
    fig.text(.5, .89, "Model tersimpan | Stratified split 80:20 | random_state=42 | Tidak melatih ulang model", ha="center", color="#56616a")
    fig.text(.07, .08, "Selisih accuracy train–test: SIBI 2,85 poin persentase dan BISINDO 2,98 poin persentase.", fontsize=13)
    fig.text(.07, .04, "Evaluasi berbasis baris dataset, bukan akurasi webcam atau pengujian lintas pengguna.", fontsize=12, color="#56616a")
    fig.subplots_adjust(top=.78, bottom=.22, wspace=.22)
    output = ROOT / "logs/design"
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "svm-train-test-metrics.png", dpi=180, facecolor="white")
    plt.close(fig)
    (output / "svm-train-test-metrics.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(pd.DataFrame(rows).to_string(index=False))
    print(output / "svm-train-test-metrics.png")


if __name__ == "__main__":
    main()
