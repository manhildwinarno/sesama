"""python audit_samples.py: replay CSV diagnosis dan uji slot pada frame identik."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent


if __name__ == "__main__":
    model, scaler, encoder = [joblib.load(ROOT / "models" / f"{name}_bisindo.joblib")
                              for name in ("best_model", "scaler", "le")]
    columns = list(scaler.feature_names_in_)
    lines = ["# Audit sampel webcam BISINDO", "",
             "Frame berurutan dalam satu rekaman bukan percobaan independen. Persentase berikut bukan akurasi generalisasi.",
             "Benar lolos: kandidat sesuai label dan skor >= ambang tersimpan. Bukan jumlah event pencatatan.", "",
             "| File | Frame | Kandidat benar | Benar lolos | Salah lolos | Skor rata-rata | Replay cocok |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    details = ["", "## Pertukaran slot pada frame identik", "",
               "Hanya frame dua tangan dengan fitur lengkap. Ini mengisolasi urutan slot dari perubahan pose antarrekaman.", ""]
    for path in sorted((ROOT / "sample").glob("*.csv")):
        data = pd.read_csv(path)
        assert data.label.isin(list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")).all(), path
        assert set(columns).issubset(data.columns), path
        valid = np.isfinite(data[columns].to_numpy()).all(axis=1)
        frame = data.loc[valid, columns]

        def predict(x):
            scaled = scaler.transform(x)
            codes = model.predict(scaled)
            guesses = encoder.inverse_transform(codes)
            indices = {v: i for i, v in enumerate(model.classes_)}
            scores = model.predict_proba(scaled)[np.arange(len(x)), [indices[v] for v in codes]]*100
            return guesses, scores

        guesses, scores = predict(frame)
        replay = (guesses == data.loc[valid, "candidate"].to_numpy()).sum()
        assert np.allclose(scores, data.loc[valid, "confidence"], atol=1e-6), path
        correct = data.candidate == data.label
        passes = data.confidence >= data.threshold
        lines.append(f"| {path.name} | {len(data)} | {correct.sum()} | {(correct & passes).sum()} | "
                     f"{(~correct & passes).sum()} | {data.confidence.mean():.1f}% | {replay}/{valid.sum()} |")
        two = valid & (data['count'] == 2)
        if two.any():
            x = data.loc[two, columns]
            swapped = pd.DataFrame(np.concatenate([x.to_numpy()[:, 63:], x.to_numpy()[:, :63]], axis=1), columns=columns)
            pred, confidence = predict(swapped)
            truth = data.loc[two, "label"].to_numpy()
            details.append(f"- {path.name}: asli benar {(data.loc[two, 'candidate'] == data.loc[two, 'label']).sum()}/{two.sum()}, "
                           f"skor {data.loc[two, 'confidence'].mean():.1f}%; ditukar benar {(pred == truth).sum()}/{two.sum()}, "
                           f"skor {confidence.mean():.1f}%; kandidat {pd.Series(pred).value_counts().to_dict()}.")
        abnormal = data.loc[(data['count'] > 2) | ~valid]
        if len(abnormal):
            details.append(f"- ANOMALI {path.name}: {len(abnormal)} frame, count={abnormal['count'].value_counts().to_dict()}; "
                           "fitur tidak lengkap tidak dimasukkan replay.")
    report = "\n".join(lines + details) + "\n"
    (ROOT / "SAMPLE_EVALUATION.md").write_text(report, encoding="utf-8")
    print(report)
