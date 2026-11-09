"""Audit CSV lokal dan artefak tepercaya: python audit_bisindo.py."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

if __name__ == "__main__":
    root = Path(__file__).resolve().parent
    model, scaler, encoder = [joblib.load(root / "models" / f"{name}_bisindo.joblib")
                              for name in ("best_model", "scaler", "le")]
    raw = pd.read_csv(root / "BISINDO/Alphabet/landmarks_train.csv")
    data = raw.drop_duplicates().reset_index(drop=True)
    x = data.drop(columns="label")
    assert list(x.columns) == list(scaler.feature_names_in_)
    assert np.isfinite(x.to_numpy()).all()
    y = data.label.map(lambda n: chr(65 + int(n)))
    _, test = train_test_split(np.arange(len(data)), test_size=.2, random_state=42, stratify=y)
    def evaluate(name, features, labels):
        pred = encoder.inverse_transform(model.predict(scaler.transform(features)))
        print(name, len(features), f"accuracy={(pred == np.asarray(labels)).mean():.4%}")
    print("raw/deduplicated", len(raw), len(data))
    zero = (x.iloc[:, 63:] == 0).all(axis=1)
    print(pd.DataFrame({"label": y, "second_hand_zero": zero}).groupby("label").agg(["sum", "count"]).to_string())
    both = x.loc[~zero]
    print("two-hand h0 wrist x < h1 wrist x", (both.h0_lm0_x < both.h1_lm0_x).mean())
    evaluate("Reconstructed notebook test", x.iloc[test], y.iloc[test])
    val = pd.read_csv(root / "BISINDO/Alphabet/landmarks_val.csv")
    training_rows = set(x.itertuples(index=False, name=None))
    overlap = np.array([row in training_rows for row in val.drop(columns="label").itertuples(index=False, name=None)])
    print("Validation rows with exact training-feature overlap", int(overlap.sum()))
    evaluate("Source validation (independence unverified)", val.drop(columns="label"), val.label.map(lambda n: chr(65 + int(n))))
    if (~overlap).any():
        separate = val.loc[~overlap]
        evaluate("Validation without exact overlap (subject/session unknown)", separate.drop(columns="label"),
                 separate.label.map(lambda n: chr(65 + int(n))))
    print("C/I/L/U/V zero-slot check")
    for letter in "CILUV":
        selected = np.flatnonzero((y == letter).to_numpy() & zero.to_numpy())[:20]
        evaluate(letter, x.iloc[selected], y.iloc[selected])
