# Evaluasi BISINDO per abjad

Evaluasi artefak tersimpan, 10 November 2026. Reproduksi: `python audit_bisindo.py`.
Tidak melatih ulang atau mengubah inferensi. Skor 65% dipakai untuk diagnosis,
bukan pengukuran kestabilan pose atau pencatatan otomatis lintas frame.

## Data

- Uji notebook: 1.284 baris dari split stratifikasi 80/20, random_state=42,
  setelah deduplikasi training; akurasi 95,9502%.
- Validasi: 1.578 baris setelah menghapus 332 baris dengan fitur identik
  training; akurasi 95,5640%. Independensi subjek/sesi tidak diketahui.
- Jumlah slot terisi berasal dari CSV, bukan verifikasi jumlah tangan pada pose asli.
- Hasil CSV bukan akurasi webcam. Sampel 20 baris C/I/L/U/V pada akhir skrip
  merupakan pemeriksaan kompatibilitas training, bukan evaluasi generalisasi.

## Akurasi per huruf

| Huruf | n uji | Uji % | n validasi | Validasi % | Salah validasi paling sering |
|---|---:|---:|---:|---:|---|
| A | 38 | 94,74 | 49 | 93,88 | X:1, Y:1, Q:1 |
| B | 46 | 91,30 | 56 | 89,29 | F:4, E:1, W:1 |
| C | 47 | 100,00 | 55 | 89,09 | P:3, D:2, O:1 |
| D | 49 | 93,88 | 64 | 95,31 | A:1, P:1, S:1 |
| E | 54 | 96,30 | 65 | 95,38 | B:3 |
| F | 47 | 97,87 | 58 | 94,83 | B:2, Y:1 |
| G | 44 | 100,00 | 49 | 97,96 | K:1 |
| H | 43 | 97,67 | 58 | 94,83 | R:2, B:1 |
| I | 59 | 100,00 | 74 | 98,65 | M:1 |
| J | 56 | 94,64 | 73 | 100,00 | - |
| K | 41 | 85,37 | 56 | 92,86 | T:3, X:1 |
| L | 50 | 100,00 | 67 | 95,52 | T:1, H:1, W:1 |
| M | 64 | 98,44 | 77 | 90,91 | N:7 |
| N | 61 | 96,72 | 74 | 93,24 | M:5 |
| O | 53 | 100,00 | 60 | 100,00 | - |
| P | 70 | 88,57 | 88 | 94,32 | D:3, W:1, Q:1 |
| Q | 40 | 87,50 | 50 | 94,00 | S:2, A:1 |
| R | 54 | 100,00 | 61 | 96,72 | S:1, C:1 |
| S | 50 | 98,00 | 60 | 98,33 | D:1 |
| T | 44 | 97,73 | 55 | 100,00 | - |
| U | 45 | 86,67 | 58 | 96,55 | R:1, P:1 |
| V | 60 | 98,33 | 70 | 98,57 | L:1 |
| W | 46 | 100,00 | 48 | 100,00 | - |
| X | 47 | 97,87 | 55 | 96,36 | A:2 |
| Y | 32 | 87,50 | 41 | 85,37 | U:3, R:1, I:1 |
| Z | 44 | 100,00 | 57 | 100,00 | - |

Prioritas pemeriksaan validasi: Y, C, B, M, K. Tidak ada kelas yang selalu
gagal pada CSV. Nilai 100% pada sampel terbatas bukan jaminan webcam.

## Diagnosis dua tangan dan kasus A

Validasi asli: satu slot 899 sampel, benar 95,7731%; dua slot 679 sampel,
benar 95,2872%. Perturbasi berikut hanya dilakukan pada 679 sampel dua slot.

| Input simulasi | Akurasi semua kelas | A benar / 47 | A menjadi D | A menjadi P |
|---|---:|---:|---:|---:|
| Asli | 95,29% | 45 | 0 | 0 |
| Slot ditukar | 83,65% | 44 | 0 | 0 |
| Hanya h0; h1 nol | 37,56% | 9 | 4 | 2 |
| Hanya h1 dipindah ke h0; h1 nol | 20,18% | 11 | 8 | 0 |

Pada A dengan hanya h0, 12 prediksi salah mencapai skor >=65%; dengan hanya
h1, 2 prediksi salah mencapai skor tersebut. Menaikkan ambang bukan solusi
lengkap. Kesalahan terbesar pada simulasi kehilangan tangan adalah A menjadi L.

Perbaikan padding tidak mengubah fitur ketika kedua tangan terdeteksi.
Perubahan perilaku terjadi saat satu tangan terdeteksi: dahulu tidak ada
prediksi, kini model menerima satu slot ditambah nol. Simulasi mendukung
kemungkinan ini untuk A menjadi D/P, tetapi tidak membuktikan penyebab webcam.
Pertukaran slot juga menurunkan akurasi keseluruhan; aturan ekstraksi sumber
belum tersedia, sehingga pengurutan otomatis belum beralasan.

## Pemeriksaan webcam berikutnya

Peragakan A, aktifkan titik tangan, catat jumlah tangan, kandidat, skor, serta
pengaturan orientasi dan pembalikan slot. Jika jumlah turun menjadi satu saat
kandidat berubah, kehilangan pelacakan mendapat bukti langsung. Jika tetap dua,
periksa landmark salah/tertutup, orientasi, urutan slot, dan perbedaan pose dari
dataset. Rekaman berlabel diperlukan untuk mengukur frekuensi kegagalan.

Jangan memblokir semua input satu tangan: L/I dan kelas satu tangan lain sudah
bekerja. Penundaan prediksi singkat saat transisi dua ke satu tangan baru layak
dipertimbangkan setelah transisi tersebut terbukti menyebabkan kesalahan;
konsekuensinya perpindahan sah ke huruf satu tangan ikut tertunda.
