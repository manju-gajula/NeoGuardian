import sys
import os
import subprocess

# Auto-detect and re-execute inside .venv if executed with global/external Python
current_dir = os.path.dirname(os.path.abspath(__file__))
venv_python = os.path.join(current_dir, ".venv", "Scripts", "python.exe")

if os.path.exists(venv_python) and os.path.normcase(os.path.abspath(sys.executable)) != os.path.normcase(os.path.abspath(venv_python)):
    # Re-launch using the project's virtual environment python
    try:
        sys.exit(subprocess.call([venv_python] + sys.argv))
    except KeyboardInterrupt:
        sys.exit(0)

# Now running safely inside the .venv with all packages installed
import webbrowser
import threading
import time
import urllib.request
import uvicorn

def wait_and_open_browser():
    """Polls health check and automatically opens the browser once ready."""
    for _ in range(30):
        try:
            req = urllib.request.urlopen("http://127.0.0.1:8000/api/health", timeout=1)
            if req.status == 200:
                print("\n[NeoGuardian] Backend is ready! Opening http://127.0.0.1:8000/ ...\n")
                webbrowser.open("http://127.0.0.1:8000/")
                break
        except Exception:
            time.sleep(0.5)

if __name__ == "__main__":
    # Ensure backend is on PYTHONPATH
    backend_dir = os.path.join(current_dir, "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    print("=" * 65)
    print("  STARTING NEOGUARDIAN CLINICAL SERVER ON http://127.0.0.1:8000")
    print("=" * 65)

    # Launch browser in a background daemon thread
    threading.Thread(target=wait_and_open_browser, daemon=True).start()

    # Start uvicorn directly in the current process
    try:
        uvicorn.run(
            "app.main:app",
            host="127.0.0.1",
            port=8000,
            reload=False,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n[NeoGuardian] Server stopped.")
