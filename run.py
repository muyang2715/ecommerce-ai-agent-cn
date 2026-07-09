"""
Launcher — starts both the FastAPI server and Streamlit UI with one command.

Usage:
    python run.py

Press Ctrl+C to stop both.
"""
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV_PYTHON = str(ROOT / "venv" / "Scripts" / "python.exe")

print("🚀 Starting Crate Support Agent...\n")

# Start FastAPI
api = subprocess.Popen(
    [VENV_PYTHON, "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=str(ROOT),
)
print(f"   ✅ FastAPI      http://localhost:8000  (PID {api.pid})")

# Start Streamlit
ui = subprocess.Popen(
    [VENV_PYTHON, "-m", "streamlit", "run", "src/ui/streamlit_app.py", "--server.port", "8501"],
    cwd=str(ROOT),
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
print(f"   ✅ Streamlit    http://localhost:8501  (PID {ui.pid})")

time.sleep(2)
webbrowser.open("http://localhost:8501")

print("\n✨ Both servers are running. Press Ctrl+C to stop.\n")

try:
    api.wait()
    ui.wait()
except KeyboardInterrupt:
    print("\n🛑 Shutting down...")
    api.terminate()
    ui.terminate()
    sys.exit(0)
