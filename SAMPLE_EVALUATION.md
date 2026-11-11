# Audit sampel webcam BISINDO

Frame berurutan dalam satu rekaman bukan percobaan independen. Persentase berikut bukan akurasi generalisasi.
Benar lolos: kandidat sesuai label dan skor >= ambang tersimpan. Bukan jumlah event pencatatan.

| File | Frame | Kandidat benar | Benar lolos | Salah lolos | Skor rata-rata | Replay cocok |
|---|---:|---:|---:|---:|---:|---:|
| bisindo_D_diagnosis.csv | 24 | 24 | 3 | 0 | 59.4% | 24/24 |
| bisindo_D_diagnosis_tukar_urutan_tangan.csv | 22 | 22 | 0 | 0 | 47.4% | 22/22 |
| bisindo_J_diagnosis_dua_tangan.csv | 20 | 0 | 0 | 10 | 60.2% | 20/20 |
| bisindo_J_diagnosis_satu_tangan.csv | 19 | 19 | 8 | 0 | 67.3% | 19/19 |
| bisindo_L_diagnosis.csv | 19 | 19 | 19 | 0 | 96.0% | 19/19 |
| bisindo_L_diagnosis_tukar_urutan_tangan.csv | 18 | 18 | 18 | 0 | 82.6% | 18/18 |
| bisindo_O_diagnosis.csv | 20 | 0 | 0 | 19 | 74.8% | 20/20 |
| bisindo_O_diagnosis_tukar_urutan_tangan.csv | 22 | 0 | 0 | 0 | 48.5% | 22/22 |
| bisindo_P_diagnosis.csv | 21 | 21 | 19 | 0 | 75.0% | 21/21 |
| bisindo_P_diagnosis_tukar_urutan_tangan.csv | 20 | 20 | 20 | 0 | 81.7% | 20/20 |
| bisindo_Q_diagnosis.csv | 23 | 23 | 23 | 0 | 74.4% | 23/23 |
| bisindo_Q_diagnosis_tukar_urutan_tangan.csv | 20 | 20 | 20 | 0 | 77.5% | 20/20 |
| bisindo_R_diagnosis.csv | 20 | 20 | 0 | 0 | 30.6% | 20/20 |
| bisindo_R_diagnosis_tukar_urutan_tangan.csv | 21 | 21 | 0 | 0 | 53.6% | 21/21 |
| bisindo_X_diagnosis.csv | 19 | 18 | 0 | 0 | 30.7% | 19/19 |
| bisindo_X_diagnosis_tukar_urutan_tangan.csv | 19 | 2 | 0 | 0 | 17.4% | 12/12 |

## Pertukaran slot pada frame identik

Hanya frame dua tangan dengan fitur lengkap. Ini mengisolasi urutan slot dari perubahan pose antarrekaman.

- bisindo_D_diagnosis.csv: asli benar 24/24, skor 59.4%; ditukar benar 24/24, skor 66.2%; kandidat {'D': 24}.
- bisindo_D_diagnosis_tukar_urutan_tangan.csv: asli benar 22/22, skor 47.4%; ditukar benar 22/22, skor 55.1%; kandidat {'D': 22}.
- bisindo_J_diagnosis_dua_tangan.csv: asli benar 0/20, skor 60.2%; ditukar benar 0/20, skor 70.4%; kandidat {'G': 20}.
- bisindo_P_diagnosis.csv: asli benar 21/21, skor 75.0%; ditukar benar 21/21, skor 87.1%; kandidat {'P': 21}.
- bisindo_P_diagnosis_tukar_urutan_tangan.csv: asli benar 20/20, skor 81.7%; ditukar benar 20/20, skor 85.7%; kandidat {'P': 20}.
- bisindo_Q_diagnosis.csv: asli benar 23/23, skor 74.4%; ditukar benar 14/23, skor 15.0%; kandidat {'Q': 14, 'P': 6, 'N': 3}.
- bisindo_Q_diagnosis_tukar_urutan_tangan.csv: asli benar 20/20, skor 77.5%; ditukar benar 20/20, skor 15.6%; kandidat {'Q': 20}.
- bisindo_X_diagnosis.csv: asli benar 18/19, skor 30.7%; ditukar benar 0/19, skor 27.0%; kandidat {'P': 19}.
- bisindo_X_diagnosis_tukar_urutan_tangan.csv: asli benar 2/8, skor 28.9%; ditukar benar 0/8, skor 19.5%; kandidat {'P': 5, 'H': 3}.
- ANOMALI bisindo_X_diagnosis_tukar_urutan_tangan.csv: 7 frame, count={3: 7}; fitur tidak lengkap tidak dimasukkan replay.
