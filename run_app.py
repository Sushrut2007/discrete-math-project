import os
import sys
import time
import threading
import webbrowser
from pathlib import Path

def open_browser():
    time.sleep(1.8)
    webbrowser.open("http://localhost:8501")

def main():
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

    print("=" * 60)
    print(" Satellite Anomaly Detection Dashboard")
    print(" Starting local server at http://localhost:8501 ...")
    print(" Opening browser automatically...")
    print(" Keep this window open while using the application.")
    print(" Close this window or press Ctrl+C to stop.")
    print("=" * 60)

    threading.Thread(target=open_browser, daemon=True).start()

    import streamlit.web.cli as stcli

    sys.argv = [
        "streamlit",
        "run",
        entry_point,
        "--global.developmentMode=false",
        "--server.headless=true",
        "--server.port=8501",
        "--browser.serverAddress=localhost",
        "--browser.gatherUsageStats=false",
    ]

    sys.exit(stcli.main())

if __name__ == "__main__":
    main()
