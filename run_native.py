import subprocess
import sys
import os

def main():
    python_exe = os.path.abspath(os.path.join("venv", "Scripts", "python.exe"))

    print("Installing uv for faster dependency resolution...")
    subprocess.run([python_exe, "-m", "pip", "install", "uv"], check=True)
    
    print("Installing backend requirements...")
    subprocess.run([python_exe, "-m", "uv", "pip", "install", "-r", "backend/requirements.txt"], check=True)

    print("Installing frontend requirements...")
    subprocess.run([python_exe, "-m", "uv", "pip", "install", "-r", "frontend/requirements.txt"], check=True)

    print("Starting backend (port 8000)...")
    backend = subprocess.Popen([python_exe, "-m", "uvicorn", "main:app", "--reload", "--port", "8000"], cwd="backend")

    print("Starting frontend (port 8501)...")
    frontend = subprocess.Popen([python_exe, "-m", "streamlit", "run", "app.py"], cwd="frontend")

    import time
    import webbrowser
    print("Waiting a few seconds for servers to start...")
    time.sleep(5)
    print("Opening browser...")
    webbrowser.open("http://localhost:8501")

    try:
        backend.wait()
        frontend.wait()
    except KeyboardInterrupt:
        print("Shutting down...")
        backend.terminate()
        frontend.terminate()

if __name__ == "__main__":
    main()
