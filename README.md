# Demo SIBI & BISINDO

Nama dan logo aplikasi belum ditentukan; header memakai placeholder `[Nama aplikasi]`. Workspace menampilkan kamera, huruf aktif, keyakinan, dan hasil ejaan. Orientasi serta pencatatan otomatis ada di sidebar; FPS/inferensi di Diagnostik. Tema terang/gelap diatur lewat menu Settings Streamlit. Restart server setelah perubahan konfigurasi tema.

Demo lokal pengenalan abjad statis MediaPipe + SVM. Jalankan `run_app.bat` atau `bash run_app.sh`; Jupyter tidak diperlukan. Launcher memakai ENV_001. Dependensi: `python -m pip install -r requirements.txt` dengan interpreter environment aplikasi.

## Kamera WebRTC
Preview kini langsung memakai stream kamera browser, target 1280×720 pada 30 FPS. Video hanya dikirim satu arah ke Python; tidak dikirim kembali untuk preview. Worker mengecilkan input hingga maksimum 640×480 dengan rasio tetap. Kamera aktual dapat memilih resolusi lebih rendah. Overlay memakai koordinat terbaru dan dapat tertinggal dari preview. Tidak ada jaminan nol latensi. Pilihan perangkat kamera sementara mengikuti perangkat default browser.

Tekan START dan izinkan kamera di browser pada http://localhost:8501. Mikrofon dimatikan. Kamera sekarang milik browser, bukan OpenCV VideoCapture. Jangan jalankan dua tab kamera sekaligus.

Worker inferensi memiliki satu slot frame terbaru, tidak menumpuk frame lama. FPS yang ditampilkan mengukur frame diterima Python, bukan FPS render browser. Inferensi dan pencatatan teks memiliki frekuensi berbeda; pose ditahan 0,5 detik dan hasil diambil panel setiap 0,2 detik.

Mirror preview terpisah dari Balik input model. Model/scaler/urutan fitur tetap sama. STOP menutup track kamera browser dan peer browser; worker inferensi tetap menunggu frame untuk START berikutnya. Pergantian mode menutup worker dan MediaPipe. ICE tanpa server eksternal ditujukan localhost; akses remote memerlukan HTTPS dan konfigurasi STUN/TURN yang ditinjau terpisah.

Suara gTTS membutuhkan internet dan mengirim teks ke Google. Hanya muat joblib tepercaya. Workaround blokir TensorFlow dipertahankan; penyebab native spesifik belum terbukti. Teks ke visual belum tersedia.

## Pengujian
`python test_camera.py` menguji negosiasi WebRTC nyata dan penerimaan minimal 90 frame sintetis tanpa browser. Ini tidak menggantikan uji izin kamera, lifecycle komponen, dan overlay di browser.
`python test_app.py` menguji callback video tetap cepat ketika worker tertahan, satu slot frame terbaru, dan cleanup. `python -m py_compile app.py video_engine.py` memeriksa sintaks. AppTest Streamlit tidak mendukung runtime sesi WebRTC secara utuh; uji browser wajib: START/STOP berulang, tombol teks/audio tidak memutus video, pergantian mode, izin kamera ditolak, orientasi input, dan FPS aktual.
