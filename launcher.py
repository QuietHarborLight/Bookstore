"""Launch the Bookstore Streamlit app (source checkout or PyInstaller bundle)."""

from __future__ import annotations

import os
import shutil
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path

APP_URL = "http://localhost:8501"


def _bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _configure_streamlit_env() -> None:
    os.environ.setdefault("STREAMLIT_GLOBAL_DEVELOPMENT_MODE", "false")
    os.environ.setdefault("STREAMLIT_SERVER_FILE_WATCHER_TYPE", "none")
    os.environ.setdefault("STREAMLIT_SERVER_HEADLESS", "true")
    os.environ.setdefault("STREAMLIT_BROWSER_GATHERUSAGESTATS", "false")


def _ensure_streamlit_config(app_dir: Path, bundle: Path) -> None:
    src = bundle / ".streamlit" / "config.toml"
    if not src.is_file():
        return

    dest_dir = app_dir / ".streamlit"
    dest_dir.mkdir(exist_ok=True)
    shutil.copy2(src, dest_dir / "config.toml")


def _wait_for_server(url: str, timeout: float = 30.0) -> bool:
    health_url = f"{url.rstrip('/')}/_stcore/health"
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=1) as response:
                if response.read() == b"ok":
                    return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.25)
    return False


def _print_banner() -> None:
    print("Bookstore Management MVP")
    print("Keep this window open while using the app.")
    print(f"Open {APP_URL} in your browser if it does not launch automatically.")
    print("Press Ctrl+C here to quit.\n")


def main() -> None:
    bundle = _bundle_dir()
    app_dir = _app_dir()
    os.chdir(app_dir)
    _configure_streamlit_env()
    _ensure_streamlit_config(app_dir, bundle)

    app_path = bundle / "app.py"
    if not app_path.is_file():
        print(f"Error: app not found at {app_path}", file=sys.stderr)
        sys.exit(1)

    _print_banner()

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--server.headless=true",
        "--global.developmentMode=false",
        "--server.fileWatcherType=none",
        "--browser.gatherUsageStats=false",
        "--browser.serverAddress=localhost",
        "--browser.serverPort=8501",
    ]

    def open_browser_when_ready() -> None:
        if _wait_for_server(APP_URL):
            webbrowser.open(APP_URL)
        else:
            print(
                "Error: Streamlit did not start within 30 seconds.",
                file=sys.stderr,
            )

    threading.Thread(target=open_browser_when_ready, daemon=True).start()

    from streamlit.web import cli as stcli

    try:
        code = stcli.main()
    except SystemExit as exc:
        code = exc.code
    if code:
        print("\nThe app stopped unexpectedly. See messages above for details.")
        input("Press Enter to close this window...")
    sys.exit(code if isinstance(code, int) else 1)


if __name__ == "__main__":
    main()
