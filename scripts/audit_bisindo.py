"""Audit CSV lokal dan artefak tepercaya: python audit_bisindo.py."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def detailed_evaluation(model, scaler, encoder, features, labels):
    """Skor CSV asli; perturbasi hanya diagnosis, bukan estimasi akurasi webcam."""
    assert list(features.columns) == list(scaler.feature_names_in_)
    assert np.isfinite(features.to_numpy()).all()
    truth = np.asarray(labels)

    def predict(frame):
        values = scaler.transform(frame)
        encoded = model.predict(values)
        pred = encoder.inverse_transform(encoded)
        columns = {label: i for i, label in enumerate(model.classes_)}
        confidence = model.predict_proba(values)[np.arange(len(frame)), [columns[p] for p in encoded]]
        return pred, confidence

    pred, confidence = predict(features)
    one = (features.iloc[:, 63:] == 0).all(axis=1).to_numpy()
    print("| Huruf | n | Benar % | Benar >=65% | Salah >=65% | Salah paling sering |")
    print("|---|---:|---:|---:|---:|---|")
    for letter in sorted(set(truth)):
        mask = truth == letter
        correct = pred == truth
        errors = pd.Series(pred[mask & ~correct]).value_counts()
        confused = ", ".join(f"{k}:{v}" for k, v in errors.head(3).items()) or "-"
        print(f"| {letter} | {mask.sum()} | {correct[mask].mean()*100:.2f} | "
              f"{(mask & correct & (confidence >= .65)).sum()} | "
              f"{(mask & ~correct & (confidence >= .65)).sum()} | {confused} |")
    for name, mask in [("Satu slot", one), ("Dua slot", ~one)]:
        if mask.any():
            print(f"{name}: n={mask.sum()}, benar={(pred[mask] == truth[mask]).mean():.4%}")

    both = features.loc[~one].copy()
    if both.empty:
        return
    expected = truth[~one]
    raw = both.to_numpy()
    variants = {
        "Asli dua tangan": raw,
        "Slot ditukar": np.concatenate([raw[:, 63:], raw[:, :63]], axis=1),
        "Hanya h0 terdeteksi": np.concatenate([raw[:, :63], np.zeros_like(raw[:, :63])], axis=1),
        "Hanya h1 terdeteksi (dipindah ke h0)": np.concatenate([raw[:, 63:], np.zeros_like(raw[:, :63])], axis=1),
    }
    for name, values in variants.items():
        guesses, scores = predict(pd.DataFrame(values, columns=features.columns))
        a = expected == "A"
        counts = pd.Series(guesses[a]).value_counts()
        print(f"{name}: n={len(values)}, benar={(guesses == expected).mean():.4%}; "
              f"A n={a.sum()}, prediksi={counts.to_dict()}, "
              f"A salah >=65%={(a & (guesses != expected) & (scores >= .65)).sum()}")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    model, scaler, encoder = [joblib.load(root / "models" / f"{name}_bisindo.joblib")
                              for name in ("best_model", "scaler", "le")]
    raw = pd.read_csv(root / "data/raw/BISINDO/Alphabet/landmarks_train.csv")
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
    detailed_evaluation(model, scaler, encoder, x.iloc[test], y.iloc[test])
    val = pd.read_csv(root / "data/raw/BISINDO/Alphabet/landmarks_val.csv")
    training_rows = set(x.itertuples(index=False, name=None))
    overlap = np.array([row in training_rows for row in val.drop(columns="label").itertuples(index=False, name=None)])
    print("Validation rows with exact training-feature overlap", int(overlap.sum()))
    evaluate("Source validation (independence unverified)", val.drop(columns="label"), val.label.map(lambda n: chr(65 + int(n))))
    if (~overlap).any():
        separate = val.loc[~overlap]
        evaluate("Validation without exact overlap (subject/session unknown)", separate.drop(columns="label"),
                 separate.label.map(lambda n: chr(65 + int(n))))
        detailed_evaluation(model, scaler, encoder, separate.drop(columns="label"),
                            separate.label.map(lambda n: chr(65 + int(n))))
    print("C/I/L/U/V zero-slot check")
    for letter in "CILUV":
        selected = np.flatnonzero((y == letter).to_numpy() & zero.to_numpy())[:20]
        evaluate(letter, x.iloc[selected], y.iloc[selected])
