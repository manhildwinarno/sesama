# Perbandingan lanjutan O/R/X

Jarak: rerata kuadrat selisih fitur setelah StandardScaler. Lebih kecil berarti lebih dekat dalam representasi model, bukan ukuran kebenaran bahasa.

## O
- Contoh O terdekat: baris CSV 4295, jarak 0.257.
- Contoh P terdekat: baris CSV 4431, jarak 0.120.
- Contoh N terdekat: baris CSV 4048, jarak 0.197.

### Sensitivitas posisi horizontal
Simulasi menggeser x seluruh tangan terisi secara bersama; slot kosong tetap nol. Bukan rekomendasi koreksi otomatis atau estimasi generalisasi.

| Pergeseran x | Kandidat benar | Skor kandidat rata-rata |
|---|---:|---:|
| -0.2 | 0/20 | 39.8% |
| -0.1 | 0/20 | 45.6% |
| +0.0 | 0/20 | 74.8% |
| +0.1 | 0/20 | 71.5% |
| +0.2 | 5/20 | 45.9% |

## R
- Contoh R terdekat: baris CSV 5336, jarak 0.116.
- Contoh H terdekat: baris CSV 2124, jarak 0.130.

### Sensitivitas posisi horizontal
Simulasi menggeser x seluruh tangan terisi secara bersama; slot kosong tetap nol. Bukan rekomendasi koreksi otomatis atau estimasi generalisasi.

| Pergeseran x | Kandidat benar | Skor kandidat rata-rata |
|---|---:|---:|
| -0.2 | 10/20 | 11.0% |
| -0.1 | 20/20 | 17.3% |
| +0.0 | 20/20 | 30.6% |
| +0.1 | 20/20 | 58.1% |
| +0.2 | 20/20 | 47.8% |

## X
- Contoh X terdekat: baris CSV 6962, jarak 0.111.
- Contoh T terdekat: baris CSV 5791, jarak 0.220.
- Contoh S terdekat: baris CSV 5502, jarak 0.171.

### Sensitivitas posisi horizontal
Simulasi menggeser x seluruh tangan terisi secara bersama; slot kosong tetap nol. Bukan rekomendasi koreksi otomatis atau estimasi generalisasi.

| Pergeseran x | Kandidat benar | Skor kandidat rata-rata |
|---|---:|---:|
| -0.2 | 0/19 | 27.7% |
| -0.1 | 0/19 | 17.0% |
| +0.0 | 18/19 | 30.7% |
| +0.1 | 19/19 | 38.0% |
| +0.2 | 0/19 | 49.0% |
