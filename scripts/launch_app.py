"""Launch on loopback; choose free port when default port is occupied."""
import socket
import subprocess
import sys
from pathlib import Path


def available_port():
    for port in range(8501, 8601):
        with socket.socket() as server:
            try:
                server.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("Tidak ada port kosong pada 8501–8600. Tutup server lama lalu coba lagi.")


if __name__ == "__main__":
    # ponytail: probe bukan reservasi; Streamlit melaporkan jika port direbut proses lain.
    port = available_port()
    print(f"Buka http://127.0.0.1:{port} · Ctrl+C untuk berhenti", flush=True)
    try:
        raise SystemExit(subprocess.call([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.address=127.0.0.1", f"--server.port={port}",
            "--server.headless=false", *sys.argv[1:],
        ], cwd=Path(__file__).resolve().parents[1]))
    except KeyboardInterrupt:
        raise SystemExit(130)
