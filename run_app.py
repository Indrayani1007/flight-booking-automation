"""
run_app.py — SkyBook Local Web Server

Serves the webapp/ directory on http://localhost:8000 using Python's
built-in http.server module (no external dependencies required).

Usage:
    python run_app.py

The server runs indefinitely until interrupted with Ctrl+C.
For CI/testing, start it as a background process before running pytest:

    # Windows PowerShell:
    Start-Process python -ArgumentList "run_app.py" -WindowStyle Hidden
    # Linux/macOS:
    python run_app.py &
"""

import http.server
import os
import socketserver
import sys

PORT = int(os.environ.get("SKYBOOK_PORT", 8000))
WEBAPP_DIR = os.path.join(os.path.dirname(__file__), "webapp")


class SilentHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP request handler that suppresses access log noise to stdout."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEBAPP_DIR, **kwargs)

    def log_message(self, format, *args):
        # Suppress per-request log lines; only startup/shutdown messages are shown
        pass


def main():
    os.chdir(WEBAPP_DIR)  # Ensure relative asset paths resolve correctly
    with socketserver.TCPServer(("", PORT), SilentHTTPHandler) as httpd:
        httpd.allow_reuse_address = True
        print(f"[SkyBook] Running at  http://localhost:{PORT}", flush=True)
        print(f"[SkyBook] Serving files from: {WEBAPP_DIR}", flush=True)
        print("[SkyBook] Press Ctrl+C to stop.", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n   Server stopped.", flush=True)
            sys.exit(0)


if __name__ == "__main__":
    main()
