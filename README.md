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

## Pengujian

`python test_camera.py` menguji server JPEG loopback: frame valid diterima, token salah, origin asing, dan isi rusak ditolak. `python test_app.py` menguji satu slot frame terbaru, resize rasio tetap, cleanup, serta regresi UI (mode default SIBI, catat manual, spasi/hapus/reset, audio, engine tetap hidup). `python -m py_compile app.py local_camera.py video_engine.py test_app.py test_camera.py` memeriksa sintaks. Uji browser tetap wajib: izin kamera, START/STOP berulang, tombol teks/audio tidak memutus kamera, pergantian mode, overlay, dan latensi nyata.
