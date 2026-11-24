"""Export chart data once: python scripts/export_evaluation.py. Never runs in the app."""
import hashlib
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import sklearn
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parents[1]


def export():
    source = ROOT / "data/processed/sibi_landmarks.csv"
    raw = pd.read_csv(source)
    clean = raw.drop_duplicates().reset_index(drop=True)
    # Local project artifacts only; never load user-supplied joblib files.
    encoder = joblib.load(ROOT / "models/le_sibi.joblib")
    scaler = joblib.load(ROOT / "models/scaler_sibi.joblib")
    model = joblib.load(ROOT / "models/best_model_sibi.joblib")
    features = clean.drop(columns="label")
    labels = encoder.transform(clean["label"])
    train, test, y_train, y_test = train_test_split(features, labels, test_size=.2, random_state=42, stratify=labels)
    assert np.allclose(scaler.mean_, train.mean(axis=0)), "Scaler does not match notebook split"
    predictions = model.predict(scaler.transform(test))
    benchmark = json.loads((ROOT / "assets/benchmark.json").read_text(encoding="utf-8"))
    recorded = benchmark["datasets"][0]
    assert (len(train), len(test)) == (recorded["train_samples"], recorded["test_samples"])
    assert round(accuracy_score(y_test, predictions), 6) == recorded["models"][0]["accuracy"]
    assert round(f1_score(y_test, predictions, average="weighted"), 6) == recorded["models"][0]["weighted_f1"]
    # Only SVM was saved. Reconstruct RF using notebook settings; label it as a rerun.
    forest = RandomForestClassifier(n_estimators=100, max_depth=15, random_state=42)
    forest.fit(scaler.transform(train), y_train)
    rf_predictions = forest.predict(scaler.transform(test))
    assert round(accuracy_score(y_test, rf_predictions), 6) == recorded["models"][1]["accuracy"]
    assert round(f1_score(y_test, rf_predictions, average="weighted"), 6) == recorded["models"][1]["weighted_f1"]
    order = np.argsort(-forest.feature_importances_)[:10]
    distributions = []
    for name, path in [("SIBI", source), ("BISINDO", ROOT / "data/raw/BISINDO/Alphabet/landmarks_train.csv")]:
        data = pd.read_csv(path)
        values = data["label"]
        if name == "BISINDO" and pd.api.types.is_numeric_dtype(values):
            values = values.map({i: chr(65 + i) for i in range(26)})
        assert values.notna().all() and set(values).issubset(set("ABCDEFGHIJKLMNOPQRSTUVWXYZ"))
        distributions.append({"dataset": name, "stage": "before deduplication", "samples": len(data),
                              "source": path.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                              "counts": {letter: int((values == letter).sum()) for letter in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"}})
    result = {
        "provenance": {"notebook": benchmark["source"], "sklearn_version": sklearn.__version__,
                       "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                       "svm_sha256": hashlib.sha256((ROOT / "models/best_model_sibi.joblib").read_bytes()).hexdigest()},
        "sibi_confusion": {"labels": encoder.classes_.tolist(), "counts": confusion_matrix(y_test, predictions).tolist(),
                           "test_samples": len(y_test), "correct": int((y_test == predictions).sum()),
                           "source": "Saved SVM predictions on reconstructed notebook test split"},
        "rf_importance": {"source": "Random Forest refitted with notebook settings; saved model scores matched to six decimals",
                          "features": [{"feature": features.columns[i], "importance": float(forest.feature_importances_[i])} for i in order]},
        "class_distributions": distributions,
    }
    (ROOT / "assets/evaluation.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f'PASS: exported verified SVM matrix ({result["sibi_confusion"]["correct"]}/{len(y_test)}), reconstructed RF importance, and raw class counts.')


if __name__ == "__main__":
    export()
