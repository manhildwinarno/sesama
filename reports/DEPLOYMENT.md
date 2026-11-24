# Streamlit Community Cloud

## Status

Transport kamera aplikasi memakai komponen Streamlit melalui koneksi aplikasi, bukan HTTP loopback. Preview tetap di browser. Frame JPEG maksimum 640×480, payload base64 maksimum 600.000 karakter, maksimum lima kiriman/detik dan satu frame menunggu acknowledgment. Batas ini bukan jaminan throughput hosting. Worker idle menutup MediaPipe setelah 60 detik; frame berikutnya membuat worker baru.

Server loopback lama masih ada untuk regresi lokal, tetapi tidak didaftarkan atau dipakai aplikasi. Model/preprocessing tidak berubah. Kamera, transkrip, worker, dan acknowledgment berada per sesi. Gambar tidak ditulis ke disk oleh aplikasi; CSV diagnosis hanya landmark/prediksi. gTTS mengirim teks ke Google.

## Sebelum deploy

1. Push branch yang sudah ditinjau ke GitHub. Jangan sertakan secrets, dataset lokal, atau log.
2. Tunggu workflow **Linux checks** lulus. `packages.txt` menyediakan library sistem OpenCV; requirements tetap dipin. Windows lolos tidak membuktikan Linux lolos.
3. Pastikan izin publikasi aset SIBI/BISINDO. Pose dan lisensi belum diverifikasi independen.
4. Untuk tugas, batasi akses aplikasi ke penguji melalui pengaturan berbagi platform jika tersedia. Pembatasan frame per sesi bukan perlindungan terhadap banyak sesi anonim; jangan anggap aplikasi tahan penyalahgunaan publik.

## Deploy

1. Masuk ke https://share.streamlit.io/ memakai akun GitHub.
2. Pilih repositori, branch yang dituju, entry point `app.py`, dan Python **3.11** pada advanced settings.
3. Deploy; periksa build/runtime logs. Jangan mematikan CORS atau XSRF protection untuk mengatasi masalah kamera.
4. Buka URL HTTPS dari perangkat/jaringan lain. Izinkan kamera; mikrofon tidak diperlukan.
5. Tes START/STOP, bahasa, mirror/landmark, teks/audio, navigasi, dan dua sesi. Ukur waktu frame pertama/inferensi; jangan memakai angka lokal sebagai angka hosting.

Jika Linux build atau kamera remote gagal, jangan mengumpulkan link sebagai selesai. Simpan video demo sebagai cadangan; layanan gratis bisa sleep atau membatasi resource. Tidak ada SLA.

## Update

Edit lokal, tes, commit, lalu push ke branch deployment. Cloud memperbarui aplikasi; perubahan dependensi dapat rebuild dan memutus sesi aktif. URL tetap selama deployment yang sama dipertahankan. Secrets hanya melalui pengaturan hosting, bukan Git.

## Tes

```powershell
python tests/test_app.py
python tests/test_camera.py
python tests/test_cloud_frames.py
node tests/check_audio.cjs
```

Dengan Playwright melalui `NODE_PATH` dan server aktif, gunakan `APP_URL` lalu `node tests/check_cloud.cjs` dan `node tests/check_design.cjs`. Tes cloud memeriksa frame Streamlit, isolasi sesi, dan tidak adanya request loopback. `tests/debug_browser.cjs` masih tes transport HTTP legacy, bukan benchmark cloud.
