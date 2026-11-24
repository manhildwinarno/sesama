from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

with st.container(key="workspace"):
    st.caption("RUANG BELAJAR / TEKS KE GRAFIS")
    heading, language = st.columns([3, 1], vertical_alignment="center")
    with heading:
        st.title("Kata punya bentuk.")
        st.caption("Ejaan huruf per huruf, bukan terjemahan tata bahasa isyarat.")
    with language:
        mode = st.segmented_control("Bahasa grafis", ["BISINDO", "SIBI"], default="BISINDO", required=True, key="visual_mode", persist_state="session")

    left, right = st.columns([2, 3], gap="large")
    with left, st.container(border=True, key="visual-input"):
        st.subheader("Mulai dari satu kata")
        text = st.text_area("Teks yang dieja", max_chars=120, placeholder="Contoh: AKU", key="visual_text", height=220, persist_state="session")
        st.button("Bersihkan", icon=":material/backspace:", on_click=lambda: st.session_state.update(visual_text=""))
        st.caption("Huruf A–Z didukung. Spasi memisahkan kata. Hasil diperbarui langsung.")
    with right, st.container(border=True, key="visual-output"):
        st.subheader("Grafis abjad")
        if not text.strip():
            st.space("large")
            st.markdown(":material/sign_language: **Ejaanmu muncul di sini**")
            st.caption("Tulis kata di panel input untuk melihat susunan grafis.")
            st.space("large")
        for number, word in enumerate(text.upper().split(), 1):
            st.caption(f"KATA {number} · {word}")
            for start in range(0, len(word), 4):
                columns = st.columns(4)
                for column, char in zip(columns, word[start:start + 4]):
                    with column:
                        path = ROOT / "assets/BISINDO" / (f"{char}.jpeg" if char == "I" else f"{char}.png") if mode == "BISINDO" and char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else None
                        if path and path.is_file():
                            st.image(str(path), caption=f"{mode} · {char}", width="stretch")
                        else:
                            with st.container(border=True):
                                st.subheader(char)
                                st.caption("Aset belum tersedia" if char in "ABCDEFGHIJKLMNOPQRSTUVWXYZ" else "Karakter belum didukung")
        st.caption("Grafis statis tidak memperagakan gerakan. BISINDO: sumber elemen Canva menurut pengguna; pose belum diverifikasi secara independen. SIBI: placeholder.")
