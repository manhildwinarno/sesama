#!/usr/bin/env bash
# Launcher aplikasi Streamlit untuk Git Bash
# Cara pakai:  ./run_app.sh
# Atau dengan argumen streamlit tambahan, misal:  ./run_app.sh --server.port 8600

set -e
cd "$(dirname "$0")" || exit 1

PYTHON="/d/software/anaconda3/envs/ENV_001/python.exe"

if [ ! -f "$PYTHON" ]; then
    echo "[ERROR] Python ENV_001 tidak ditemukan di: $PYTHON"
    exit 1
fi

echo "Menjalankan aplikasi Streamlit..."
echo "Tekan Ctrl+C untuk menghentikan server."
echo

exec "$PYTHON" -m streamlit run app.py "$@"
