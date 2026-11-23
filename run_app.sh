#!/usr/bin/env bash
# Launcher aplikasi Streamlit untuk Git Bash
# Cara pakai:  ./run_app.sh
# Atau dengan argumen streamlit tambahan, misal:  ./run_app.sh --server.port 8600

set -e
cd "$(dirname "$0")" || exit 1

PYTHON="${PYTHON:-.venv/Scripts/python.exe}"

if [ ! -f "$PYTHON" ]; then
    echo "[ERROR] Python proyek tidak ditemukan di: $PYTHON"
    echo "Buat environment: py -3.11 -m venv .venv"
    echo "Instal dependensi: .venv/Scripts/python.exe -m pip install -r requirements.txt"
    exit 1
fi

echo "Menjalankan aplikasi Streamlit..."
echo "Tekan Ctrl+C untuk menghentikan server."
echo

exec "$PYTHON" -m streamlit run app.py "$@"
