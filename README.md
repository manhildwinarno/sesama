# Isyarat: SIBI & BISINDO

Demo lokal pengenalan abjad statis berbasis MediaPipe dan SVM. Bukan penerjemah tata bahasa isyarat.

Jalankan `run_app.bat` di Windows atau `bash run_app.sh` di Git Bash. Launcher memakai Python ENV_001. Jupyter tidak perlu menyala. Instal dependensi dengan Python environment aplikasi: `python -m pip install -r requirements.txt`.

Kamera menggunakan webcam komputer server. Teks dikirim ke Google saat fitur suara dipakai; gTTS membutuhkan internet. Jangan membuka aplikasi ke jaringan publik tanpa meninjau akses dan privasi. Hanya muat artefak joblib tepercaya.

Resource kamera bertahan per sesi saat tombol ditekan. Tekan Hentikan kamera sebelum meninggalkan halaman. Penutupan saat sesi browser hilang bergantung pada pembersihan resource Python; jangan mengandalkannya untuk aplikasi multiuser.

Mirror preview tidak mengubah input model. Jika orientasi tidak cocok dataset, bandingkan opsi Balik input model. Urutan BISINDO dapat diuji lewat Tukar urutan tangan; urutan kanonis dan dukungan tangan kanan/kiri belum tervalidasi terhadap data latih.

Halaman menampilkan durasi webcam dibuka, frame pertama, inisialisasi MediaPipe, dan proses frame. Interval fragment 100 ms bukan klaim 30 FPS. Suara sinkron dapat menjeda frame selama permintaan jaringan, tetapi tidak menutup kamera.

Uji regresi tanpa hardware: `python test_app.py`. Uji manual: mulai kamera, tekan spasi/hapus/reset/suara, pastikan feed lanjut tanpa start ulang; coba stop/start, pergantian mode, dan orientasi input. UI teks ke visual ditunda sampai aset berizin tersedia.
