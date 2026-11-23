"""python compare_samples.py: bandingkan fitur webcam O/R/X dengan training."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from visualize_bisindo import skeleton

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    model, scaler, encoder = [joblib.load(ROOT / "models" / f"{name}_bisindo.joblib")
                              for name in ("best_model", "scaler", "le")]
    cols = list(scaler.feature_names_in_)
    train = pd.read_csv(ROOT / "data/raw/BISINDO/Alphabet/landmarks_train.csv").drop_duplicates()
    raw = train[cols].to_numpy()
    scaled = scaler.transform(train[cols])
    html = ['<!doctype html><meta charset="utf-8"><title>Perbandingan sampel BISINDO</title>',
            '<style>body{font:16px sans-serif;margin:24px}section{display:flex;flex-wrap:wrap}figure{width:280px;margin:8px;border:1px solid #aaa}svg{width:100%}</style>',
            '<h1>Webcam dibanding training</h1><p>Koordinat input model, bukan preview mirror. Hijau h0, ungu h1. Gambar menampilkan x/y; pencarian memakai seluruh x/y/z setelah scaler. Contoh terdekat bukan verifikasi kebenaran label atau pose.</p>']
    report = ['# Perbandingan lanjutan O/R/X', '',
              'Jarak: rerata kuadrat selisih fitur setelah StandardScaler. Lebih kecil berarti lebih dekat dalam representasi model, bukan ukuran kebenaran bahasa.', '']
    for letter, alternatives in [('O', 'OPN'), ('R', 'RH'), ('X', 'XTS')]:
        data = pd.read_csv(ROOT / 'data/samples' / f'bisindo_{letter}_diagnosis.csv')
        features = data[cols].to_numpy()
        assert np.isfinite(features).all()
        values = scaler.transform(data[cols])
        # Pilih frame nyata terdekat dengan pusat rekaman, bukan pose sintetis rata-rata.
        representative = np.square(values - values.mean(axis=0)).mean(axis=1).argmin()
        html.append(f'<h2>{letter}</h2><section><figure>{skeleton(features[representative])}<figcaption>Webcam frame {representative+1}; kandidat {data.iloc[representative].candidate}</figcaption></figure>')
        report.append(f'## {letter}')
        for alternative in alternatives:
            ids = np.flatnonzero(train.label.to_numpy() == ord(alternative)-65)
            distances = np.square(values[:, None, :] - scaled[ids][None, :, :]).mean(axis=2).mean(axis=0)
            for rank, local in enumerate(np.argsort(distances)[:3], 1):
                index = ids[local]
                row = int(train.index[index])+2
                html.append(f'<figure>{skeleton(raw[index])}<figcaption>Training {alternative}, #{rank}; baris {row}; jarak {distances[local]:.3f}</figcaption></figure>')
                if rank == 1:
                    report.append(f'- Contoh {alternative} terdekat: baris CSV {row}, jarak {distances[local]:.3f}.')
        html.append('</section>')
        report.extend(['', '### Sensitivitas posisi horizontal',
                       'Simulasi menggeser x seluruh tangan terisi secara bersama; slot kosong tetap nol. Bukan rekomendasi koreksi otomatis atau estimasi generalisasi.', '',
                       '| Pergeseran x | Kandidat benar | Skor kandidat rata-rata |', '|---|---:|---:|'])
        points = features.reshape(-1, 2, 21, 3)
        present = np.any(points != 0, axis=(2, 3))
        for shift in [-.2, -.1, 0, .1, .2]:
            changed = points.copy()
            changed[:, :, :, 0] += shift * present[:, :, None]
            assert np.array_equal(changed[~present], points[~present])
            frame = pd.DataFrame(changed.reshape(-1, 126), columns=cols)
            transformed = scaler.transform(frame)
            codes = model.predict(transformed)
            pred = encoder.inverse_transform(codes)
            probabilities = model.predict_proba(transformed)
            indices = {code: i for i, code in enumerate(model.classes_)}
            confidence = probabilities[np.arange(len(codes)), [indices[c] for c in codes]]*100
            report.append(f'| {shift:+.1f} | {(pred == letter).sum()}/{len(pred)} | {confidence.mean():.1f}% |')
        report.append('')
    (ROOT / 'reports/galleries/sample_comparison.html').write_text('\n'.join(html), encoding='utf-8')
    text = '\n'.join(report)
    (ROOT / 'reports/SAMPLE_COMPARISON.md').write_text(text, encoding='utf-8')
    print(text)
