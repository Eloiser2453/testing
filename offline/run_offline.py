from __future__ import annotations

import http.server
import socketserver
import webbrowser
from functools import partial
from pathlib import Path


def main() -> None:
    directory = Path(__file__).resolve().parent
    handler = partial(
        http.server.SimpleHTTPRequestHandler, directory=str(directory)
    )

    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        port = httpd.server_address[1]
        base_url = f"http://127.0.0.1:{port}"
        print(f"Serving offline app at {base_url}")
        print("Press Ctrl+C to stop.")
        webbrowser.open(f"{base_url}/form.html")
        webbrowser.open(f"{base_url}/print.html")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
