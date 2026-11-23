# Audit set landmark tambahan

Pengguna mengonfirmasi satu tangan dan pose ditahan pada rekaman O/R terbaru. Analisis hanya frame dengan count=2. Jarak memakai koordinat gambar ternormalisasi, bukan piksel atau jarak fisik.

## O: 20 frame
- Median jarak pergelangan x/y: 0.3416.
- Median jarak landmark berindeks sama x/y: 0.0794.

| Input | Kandidat | Skor rata-rata | Rentang skor | Benar >=65% |
|---|---|---:|---:|---:|
| Asli | {'S': 11, 'K': 9} | 42.2% | 18.9–92.2% | 0 |
| h0 saja | {'G': 20} | 30.8% | 19.0–64.8% | 0 |
| h1 dipindah ke h0 | {'P': 20} | 86.4% | 69.1–92.7% | 0 |

## R: 1 frame
- Median jarak pergelangan x/y: 0.0759.
- Median jarak landmark berindeks sama x/y: 0.0102.

| Input | Kandidat | Skor rata-rata | Rentang skor | Benar >=65% |
|---|---|---:|---:|---:|
| Asli | {'H': 1} | 25.7% | 25.7–25.7% | 0 |
| h0 saja | {'R': 1} | 28.3% | 28.3–28.3% | 0 |
| h1 dipindah ke h0 | {'H': 1} | 16.1% | 16.1–16.1% | 0 |

## Kesimpulan
- Menghapus satu slot tidak memulihkan O: h0 menjadi G, h1 menjadi P. Deteksi tambahan bukan satu-satunya masalah yang dapat diselesaikan dengan membuang slot.
- Pada satu frame R, kedua set berdekatan pada banyak landmark; konsisten dengan kemungkinan pelacakan ganda, belum bukti tanpa frame kamera tersinkron. h0 saja menghasilkan R tetapi tetap di bawah ambang.
- Jangan memilih slot berdasarkan skor maksimum: pada O, slot h1 menghasilkan P yang salah dengan skor tinggi.
- Belum menerapkan deduplikasi otomatis. Perlu frame kamera tersinkron dengan dua set landmark untuk membedakan deteksi ganda, landmark keliru, dan sumber visual lain.
