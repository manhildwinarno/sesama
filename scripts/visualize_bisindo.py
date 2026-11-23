"""python visualize_bisindo.py: galeri HTML landmark training lokal, tanpa dependensi baru."""
from pathlib import Path
import pandas as pd
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from video_engine import CONNECTIONS


def skeleton(values):
    parts = ['<svg viewBox="0 0 300 300" role="img" aria-label="Landmark CSV">']
    for slot, color in enumerate(("#176b45", "#a13d86")):
        points = values[slot*63:(slot+1)*63].reshape(21, 3)
        if not points.any():
            continue
        for a, b in CONNECTIONS:
            x, y = points[a, :2]*300
            xx, yy = points[b, :2]*300
            parts.append(f'<line x1="{x}" y1="{y}" x2="{xx}" y2="{yy}" stroke="{color}"/>')
        for i, (x, y, _) in enumerate(points):
            parts.append(f'<circle cx="{x*300}" cy="{y*300}" r="2" fill="{color}"/><text x="{x*300+3}" y="{y*300}" font-size="8">{i}</text>')
    return "".join(parts) + "</svg>"


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    data = pd.read_csv(root / "data/raw/BISINDO/Alphabet/landmarks_train.csv").drop_duplicates()
    html = ['<!doctype html><meta charset="utf-8"><title>Landmark BISINDO</title>',
            '<style>body{font:16px sans-serif;margin:24px}section{display:flex;flex-wrap:wrap}figure{width:260px;margin:8px;border:1px solid #bbb}svg{width:100%}</style>',
            '<h1>Sampel training BISINDO</h1><p>Koordinat x/y asli, y ke bawah. Hijau: h0; ungu: h1. Angka: indeks landmark. Bukan panduan pose terverifikasi; z tidak ditampilkan. Sampel dipilih merata menurut urutan baris, bukan menurut skor model.</p>']
    for letter in "DSJONPQRHXTLC":
        group = data.loc[data.label == ord(letter)-65]
        html.append(f'<h2>{letter}</h2><section>')
        for index in sorted(set(round(i*(len(group)-1)/5) for i in range(6))):
            row = group.iloc[index]
            values = row.drop("label").to_numpy(dtype=float)
            html.append(f'<figure>{skeleton(values)}<figcaption>Baris CSV {row.name+2}; slot terisi {1 + int(values[63:].any())}</figcaption></figure>')
        html.append('</section>')
    target = root / "reports/galleries/bisindo_landmarks.html"
    target.write_text("\n".join(html), encoding="utf-8")
    print(target)
