import streamlit as st

with st.container(key="workspace"):
    st.caption("RUANG BELAJAR / PANDUAN")
    st.title("Kenali abjad, langkah demi langkah.")
    with st.container(border=True):
        st.subheader("Isyarat ke teks")
        st.markdown("1. Pilih SIBI atau BISINDO, lalu tekan **START** dan izinkan kamera.\n2. Pastikan tangan dan jari terlihat, dengan pencahayaan merata.\n3. Tahan pose hingga huruf tercatat. Lepaskan tangan sebelum mengulang huruf sama.\n4. Gunakan Spasi, Hapus, dan Reset untuk merangkai teks. Tekan **STOP** saat selesai.")
        st.caption("Cerminkan preview hanya mengubah tampilan. Balik input model mengubah gambar inferensi. Urutan tangan BISINDO harus sesuai training; dukungan kedua tangan belum tervalidasi.")
    with st.container(border=True):
        st.subheader("Teks ke grafis")
        st.write("Tulis hingga 120 karakter. A–Z dieja per huruf, spasi memisahkan kata. SIBI memakai placeholder sampai aset dan pose terverifikasi tersedia.")
        st.caption("Aplikasi mengenali abjad statis, bukan tata bahasa atau gerakan dinamis. Rekaman suara belum tersedia.")
    with st.container(border=True):
        st.subheader("Privasi dan batas penggunaan")
        st.write("Mikrofon dimatikan. Preview kamera tetap di browser; frame JPEG dikirim ke server lokal untuk inferensi. CSV diagnosis berisi landmark dan prediksi, tanpa gambar.")
        st.write("Bunyikan teks memerlukan internet dan mengirim teks ke Google melalui gTTS. Gunakan aplikasi di localhost; akses remote memerlukan rancangan keamanan terpisah.")
        st.caption("Metrik evaluasi yang dilaporkan: SIBI 95,92%, BISINDO 95,95%. Bukan jaminan akurasi webcam. Pose, posisi, pencahayaan, dan kesesuaian training memengaruhi hasil.")
