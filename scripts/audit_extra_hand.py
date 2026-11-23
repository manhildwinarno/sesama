"""python audit_extra_hand.py: ablation slot pada O/R terbaru, tanpa ubah model."""
from pathlib import Path
import joblib
import numpy as np
import pandas as pd

if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    model, scaler, encoder = [joblib.load(root / 'models' / f'{name}_bisindo.joblib')
                              for name in ('best_model', 'scaler', 'le')]
    columns = list(scaler.feature_names_in_)
    output = ['# Audit set landmark tambahan', '',
              'Pengguna mengonfirmasi satu tangan dan pose ditahan pada rekaman O/R terbaru. '
              'Analisis hanya frame dengan count=2. Jarak memakai koordinat gambar ternormalisasi, bukan piksel atau jarak fisik.', '']
    for letter in 'OR':
        data = pd.read_csv(root / 'data/samples' / f'bisindo_{letter}_diagnosis_terbaru.csv')
        data = data.loc[data['count'] == 2]
        raw = data[columns].to_numpy()
        assert len(raw) and np.isfinite(raw).all()
        points = raw.reshape(-1, 2, 21, 3)
        wrist = np.linalg.norm(points[:, 0, 0, :2] - points[:, 1, 0, :2], axis=1)
        distance = np.linalg.norm(points[:, 0, :, :2] - points[:, 1, :, :2], axis=2)
        output.extend([f'## {letter}: {len(raw)} frame',
                       f'- Median jarak pergelangan x/y: {np.median(wrist):.4f}.',
                       f'- Median jarak landmark berindeks sama x/y: {np.median(distance):.4f}.', '',
                       '| Input | Kandidat | Skor rata-rata | Rentang skor | Benar >=65% |',
                       '|---|---|---:|---:|---:|'])
        for name, values in [('Asli', raw),
                             ('h0 saja', np.concatenate([raw[:, :63], np.zeros_like(raw[:, :63])], axis=1)),
                             ('h1 dipindah ke h0', np.concatenate([raw[:, 63:], np.zeros_like(raw[:, :63])], axis=1))]:
            scaled = scaler.transform(pd.DataFrame(values, columns=columns))
            codes = model.predict(scaled)
            guesses = encoder.inverse_transform(codes)
            probabilities = model.predict_proba(scaled)
            indices = {v: i for i, v in enumerate(model.classes_)}
            scores = probabilities[np.arange(len(codes)), [indices[c] for c in codes]]*100
            if name == 'Asli':
                assert np.array_equal(guesses, data.candidate.to_numpy())
                assert np.allclose(scores, data.confidence.to_numpy())
            else:
                assert (values[:, 63:] == 0).all()
            output.append(f'| {name} | {pd.Series(guesses).value_counts().to_dict()} | {scores.mean():.1f}% | '
                          f'{scores.min():.1f}–{scores.max():.1f}% | {((guesses == letter) & (scores >= 65)).sum()} |')
        output.append('')
    output.extend(['## Kesimpulan',
                   '- Menghapus satu slot tidak memulihkan O: h0 menjadi G, h1 menjadi P. Deteksi tambahan bukan satu-satunya masalah yang dapat diselesaikan dengan membuang slot.',
                   '- Pada satu frame R, kedua set berdekatan pada banyak landmark; konsisten dengan kemungkinan pelacakan ganda, belum bukti tanpa frame kamera tersinkron. h0 saja menghasilkan R tetapi tetap di bawah ambang.',
                   '- Jangan memilih slot berdasarkan skor maksimum: pada O, slot h1 menghasilkan P yang salah dengan skor tinggi.',
                   '- Belum menerapkan deduplikasi otomatis. Perlu frame kamera tersinkron dengan dua set landmark untuk membedakan deteksi ganda, landmark keliru, dan sumber visual lain.'])
    report = '\n'.join(output) + '\n'
    (root / 'reports/EXTRA_HAND_EVALUATION.md').write_text(report, encoding='utf-8')
    print(report)
