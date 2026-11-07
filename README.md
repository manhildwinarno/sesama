# Isyarat: SIBI & BISINDO

Demo lokal pengenalan abjad statis MediaPipe + SVM. Jalankan `run_app.bat` atau `bash run_app.sh`; Jupyter tidak diperlukan. Launcher memakai ENV_001. Dependensi: `python -m pip install -r requirements.txt` dengan interpreter environment aplikasi.

## Kamera WebRTC
Tekan START dan izinkan kamera di browser pada http://localhost:8501. Mikrofon dimatikan. Kamera sekarang milik browser, bukan OpenCV VideoCapture. Jangan jalankan dua tab kamera sekaligus.

Target kamera 640×480, 30 FPS (maksimum permintaan 60); bukan jaminan FPS. Callback video hanya meneruskan frame dengan mirror opsional. Worker inferensi memiliki satu slot frame terbaru, tidak menumpuk frame lama. Preview tidak memuat skeleton agar video tidak menunggu MediaPipe. FPS yang ditampilkan mengukur callback video masuk, bukan FPS render browser. Inferensi dan pencatatan teks memiliki frekuensi berbeda; pose ditahan 0,5 detik dan hasil diambil panel setiap 0,2 detik.

Mirror preview terpisah dari Balik input model. Model/scaler/urutan fitur tetap sama. STOP, putus koneksi, atau pergantian mode menutup worker dan MediaPipe. ICE tanpa server eksternal ditujukan localhost; akses remote memerlukan HTTPS dan konfigurasi STUN/TURN yang ditinjau terpisah.

Suara gTTS membutuhkan internet dan mengirim teks ke Google. Hanya muat joblib tepercaya. Workaround blokir TensorFlow dipertahankan; penyebab native spesifik belum terbukti. Teks ke visual belum tersedia.

## Pengujian
`python test_app.py` menguji callback video tetap cepat ketika worker tertahan, satu slot frame terbaru, dan cleanup. `python -m py_compile app.py video_engine.py` memeriksa sintaks. AppTest Streamlit tidak mendukung runtime sesi WebRTC secara utuh; uji browser wajib: START/STOP berulang, tombol teks/audio tidak memutus video, pergantian mode, izin kamera ditolak, orientasi input, dan FPS aktual.
