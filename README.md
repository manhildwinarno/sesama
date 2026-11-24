# Demo SIBI & BISINDO

Nama dan logo aplikasi belum ditentukan; header memakai placeholder `[Nama aplikasi]`. Workspace menampilkan kamera, huruf aktif, keyakinan, dan hasil ejaan. Orientasi serta pencatatan otomatis ada di sidebar; FPS/inferensi di Diagnostik. Tema terang/gelap diatur lewat menu Settings Streamlit. Restart server setelah perubahan konfigurasi tema.

Demo lokal pengenalan abjad statis MediaPipe + SVM. Jalankan `run_app.bat` atau `bash run_app.sh`; Jupyter tidak diperlukan. Launcher memakai ENV_001. Dependensi: `python -m pip install -r requirements.txt` dengan interpreter environment aplikasi. `streamlit-webrtc`/`av` tidak lagi dipakai aplikasi ini walaupun mungkin masih terpasang di environment lama.

## Kamera lokal

Preview memakai stream kamera browser langsung, target 1280×720 pada 30 FPS. Preview tidak melewati Python, jadi tidak menunggu inferensi. Kamera aktual dapat memilih resolusi lebih rendah.

Frame untuk inferensi diperkecil di browser hingga maksimum 640×480 (rasio tetap), dikodekan JPEG, lalu dikirim ke server HTTP loopback dengan interval maksimum sekitar 10 frame/detik. Fetch dibatalkan setelah 2,5 detik dan dicoba lagi; URL/token terbaru dibaca ulang saat komponen diperbarui. Hanya ada satu slot frame terbaru; frame lama tidak menumpuk. FPS di Diagnostik mengukur frame yang diterima Python, bukan render preview. Diagnostik juga menampilkan waktu frame terakhir.

Server frame mengikat `127.0.0.1` pada port acak dan memakai token per sesi. Origin selain localhost dan isi non-JPEG ditolak. Ini transport lokal, bukan API publik. Akses dari perangkat lain memerlukan HTTPS, autentikasi, dan rancangan terpisah.

Tekan START dan izinkan kamera di browser pada http://localhost:8501. Mikrofon dimatikan. Jangan jalankan dua tab kamera sekaligus.

Pose ditahan 0,4 detik sebelum huruf dicatat; panel hasil diperbarui sekitar 0,1 detik. Mirror preview terpisah dari Balik input model. Model/scaler/urutan fitur tetap sama. STOP menghentikan kamera browser dan pengiriman frame; worker inferensi tetap menunggu frame untuk START berikutnya. Pergantian mode menutup worker dan MediaPipe. Titik tangan memakai koordinat worker terakhir, diperbarui sekitar 0,15 detik, sehingga dapat tertinggal saat tangan bergerak cepat.

Suara gTTS membutuhkan internet dan mengirim teks ke Google. Hanya muat joblib tepercaya. Workaround blokir TensorFlow dipertahankan; penyebab native spesifik belum terbukti. Teks ke visual belum tersedia.

## Struktur repositori

| Folder | Isi |
|---|---|
| `notebooks/` | Inspeksi/ekstraksi, EDA/preprocessing, training/evaluasi; jalankan urut 01–03 |
| `data/raw/` | Dataset asli lokal (tidak diunggah) |
| `data/processed/` | CSV landmark hasil preprocessing (lokal) |
| `data/samples/` | Sampel diagnosis webcam (lokal) |
| `models/` | Model, scaler, dan label encoder aplikasi |
| `assets/` | Grafis abjad aplikasi |
| `scripts/` | Skrip audit dan visualisasi; jalankan dari root, misalnya `python scripts/audit_samples.py` |
| `tests/` | `python tests/test_app.py`, `python tests/test_camera.py`, dan regresi browser |
| `reports/` | Laporan audit, `figures/` hasil plot, `galleries/` visualisasi HTML |
| `app_pages/` | Halaman isyarat, grafis, dan panduan melalui `st.navigation`; entry point `app.py` |
| `static/` | Font Inter lokal dan lisensi; tidak membutuhkan Google Fonts |
| `logs/` | Log lokal, tidak diunggah |

Notebook menemukan root proyek dari working directory root atau subfoldernya. Path data dan output sudah mengikuti struktur di atas. Notebook training dapat menimpa artefak `models/` jika dijalankan; penataan folder tidak menjalankan training. DLL merupakan bagian environment/dependensi, bukan kode aplikasi; tidak ada DLL ditemukan pada penataan ini.

Launcher memakai `.venv/Scripts/python.exe` secara default; variabel lingkungan `PYTHON` dapat mengganti lokasi interpreter. Aset BISINDO saat ini tersedia A–Z, SIBI masih placeholder.

### Environment Windows

Gunakan Python 3.11 untuk dependensi yang dipin proyek. Python 3.14 boleh tetap terpasang untuk proyek lain.

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
.\run_app.bat
```

Git Bash: `bash run_app.sh`. Aktivasi environment tidak wajib karena launcher memakai interpreter `.venv` langsung. Environment ini untuk aplikasi dan tes; notebook training dapat membutuhkan paket tambahan yang tidak termasuk requirements aplikasi.

## Pengujian

## Teks ke grafis

Pilih **Teks ke grafis** pada sidebar, pilih BISINDO/SIBI, lalu masukkan teks maksimal 120 karakter. Huruf ditampilkan berurutan per kata. Aset BISINDO saat ini hanya I (`assets/BISINDO/I.jfif`) dan Q (`assets/BISINDO/17.png`); huruf lainnya serta seluruh SIBI memakai placeholder. Angka/tanda baca diberi keterangan belum didukung. Sumber grafis menurut pengguna: elemen Canva; pose belum diverifikasi secara independen. Ini ejaan abjad statis, bukan terjemahan tata bahasa. Rekaman suara belum tersedia. Berpindah ke mode grafis menutup worker kamera dan melepas registrasi server sesi.

### Audit BISINDO

Visualisasi: `python visualize_bisindo.py`, lalu buka `bisindo_landmarks.html` di browser. Galeri menampilkan enam sampel per huruf untuk pasangan bermasalah dan pembanding; warna membedakan slot, angka menunjukkan indeks landmark. Koordinat x/y asli, bukan panduan pose terverifikasi.

Diagnosis webcam: pilih BISINDO, buka **Rekam sampel diagnosis**, pilih huruf tujuan, tahan pose, tekan **Rekam 5 detik**, lalu **Unduh CSV diagnosis**. Rekam D/J/O/P/Q/R/X serta L sebagai pembanding. CSV berisi fitur sebelum scaler, kandidat/skor, jumlah tangan dan pengaturan; tanpa gambar. Unduh setiap percobaan sebelum merekam ulang atau mengganti mode. Simpan kedua variasi J sebagai file terpisah. Rekaman ini belum otomatis mengubah dataset/model.

Jalankan `python audit_bisindo.py` dengan CSV lokal dan artefak model tepercaya. Dataset training berisi 7.558 baris (6.419 setelah deduplikasi). Rekonstruksi split notebook menghasilkan akurasi 95,9502% pada 1.284 baris. Validasi sumber mencapai 96,3351% pada 1.910 baris, tetapi 332 baris memiliki fitur identik dengan training. Setelah overlap persis dibuang: 95,5640% pada 1.578 baris; independensi subjek/sesi belum diketahui. Angka ini bukan akurasi webcam.

CSV menyimpan input satu tangan pada 63 fitur `h0`, lalu 63 nol pada `h1`. Worker kini memakai padding tersebut sebelum StandardScaler; tanpa tangan tidak diklasifikasikan. Tes memeriksa padding, urutan dua tangan termasuk toggle pembalikan, kandidat/event, serta input SIBI. Panduan UI menerima satu atau dua tangan BISINDO dan menampilkan jumlah tangan terdeteksi.

Kode ekstraksi asli BISINDO tidak tersedia di folder dataset lokal. Pada sampel dua tangan, `h0_lm0_x < h1_lm0_x` terjadi 49,81%; ini tidak mendukung asumsi slot selalu diurutkan menurut posisi horizontal. Konvensi handedness/orientasi belum terverifikasi. Uji webcam C/I/L/U/V lalu A–Z; catat jumlah tangan, kandidat, skor, orientasi input, dan toggle urutan. Training ulang dipertimbangkan setelah konvensi ekstraksi dicocokkan dan evaluasi webcam tetap buruk.

Regresi browser: jalankan server di port 8511, lalu `node debug_browser.cjs` dengan Playwright tersedia melalui `NODE_PATH` (atau instalasi lokal). `APP_URL` dapat mengganti URL server. Tes memakai webcam sintetis Chromium, memeriksa aliran frame sekitar 90 detik, toggle, STOP/START, serta piksel overlay dengan koordinat simulasi. Ini bukan uji akurasi pose. Komponen kamera berada di luar fragment; overlay dikirim dalam respons POST frame. Hanya panel hasil polling setiap 0,3 detik. Restart server setelah perubahan handler HTTP agar handler lama tidak tetap hidup.

`python tests/test_camera.py` menguji server JPEG loopback: frame valid diterima, token salah, origin asing, dan isi rusak ditolak. `python tests/test_app.py` menguji satu slot frame terbaru, resize rasio tetap, cleanup, kontrol teks/audio, navigasi halaman, pilihan bahasa, dan slider tanpa mengganti engine. `python -m compileall -q app.py app_pages local_camera.py video_engine.py tests` memeriksa sintaks. Jika Playwright tersedia, `node tests/check_design.cjs` mengambil screenshot ke `logs/design/` dan memeriksa font, overflow mobile, kamera saat pengaturan berubah, serta penutupan track saat navigasi. Atur `NODE_PATH` ke lokasi Playwright dan `APP_URL` jika bukan `http://localhost:8511`. Uji webcam fisik tetap wajib: izin kamera, START/STOP, pose, dan latensi nyata.
