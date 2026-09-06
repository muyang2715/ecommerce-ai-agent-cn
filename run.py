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
# Reuse the interpreter that launched this script. This keeps the upstream
# Windows workflow working and also supports macOS/Linux virtual environments.
VENV_PYTHON = sys.executable

print("🚀 正在启动 Crate 中文智能客服...\n")

# Start FastAPI
api = subprocess.Popen(
    [VENV_PYTHON, "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=str(ROOT),
)
print(f"   ✅ FastAPI      http://localhost:8000 （进程 {api.pid}）")

# Start Streamlit
ui = subprocess.Popen(
    [
        VENV_PYTHON,
        "-m",
        "streamlit",
        "run",
        "src/ui/streamlit_app.py",
        "--server.port",
        "8501",
        "--server.headless",
        "true",
    ],
    cwd=str(ROOT),
)
print(f"   ✅ Streamlit    http://localhost:8501 （进程 {ui.pid}）")

time.sleep(2)
webbrowser.open("http://localhost:8501")

print("\n✨ 两个服务均已启动，按 Ctrl+C 停止。\n")

try:
    api.wait()
    ui.wait()
except KeyboardInterrupt:
    print("\n🛑 正在停止服务...")
    api.terminate()
    ui.terminate()
    sys.exit(0)
