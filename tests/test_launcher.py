"""Run: .venv/Scripts/python.exe tests/test_launcher.py"""
import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from launch_app import available_port

with socket.socket() as occupied:
    occupied.bind(("127.0.0.1", 0))
    port = available_port()
    assert 8501 <= port <= 8600
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", port))

with socket.socket() as occupied:
    try:
        occupied.bind(("127.0.0.1", 8501))
    except OSError:
        pass
    assert available_port() != 8501
print("OK: port kosong dan fallback saat 8501 terpakai.")
