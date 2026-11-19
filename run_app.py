import os
import sys
import time
import socket
import threading
import webbrowser
from pathlib import Path

def find_available_port(preferred_port=8501):
    """Finds an open port starting from preferred_port."""
    for port in range(preferred_port, preferred_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(('127.0.0.1', port))
                return port
            except OSError:
                continue
    return 8501

def open_browser(port):
    time.sleep(2.0)
    webbrowser.open(f"http://localhost:{port}")

def main():
    try:
        # Determine base directory whether running as script or frozen executable
        if getattr(sys, "frozen", False):
            base_dir = Path(sys._MEIPASS)
        else:
            base_dir = Path(__file__).resolve().parent

        # Ensure base_dir, src, and app are in sys.path
        if str(base_dir) not in sys.path:
            sys.path.insert(0, str(base_dir))
        app_dir = base_dir / "app"
        if str(app_dir) not in sys.path:
            sys.path.insert(0, str(app_dir))

        entry_point = str(base_dir / "app" / "1_Overview.py")
        port = find_available_port(8501)

        print("=" * 60)
        print(" Satellite Anomaly Detection Dashboard")
        print(f" Starting local server at http://localhost:{port} ...")
        print(" Opening browser automatically...")
        print(" Keep this window open while using the application.")
        print(" Close this window or press Ctrl+C to stop.")
        print("=" * 60)

        threading.Thread(target=open_browser, args=(port,), daemon=True).start()

        import streamlit.web.cli as stcli

        sys.argv = [
            "streamlit",
            "run",
            entry_point,
            "--global.developmentMode=false",
            "--server.headless=true",
            f"--server.port={port}",
            "--browser.serverAddress=localhost",
            "--browser.gatherUsageStats=false",
        ]

        sys.exit(stcli.main())
    except Exception as e:
        print(f"\nError occurred while starting application: {e}")
        import traceback
        traceback.print_exc()
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()
