"""테스트 사이트를 띄운다. view.html?id=1024 같은 주소를 파일로 이어준다."""
import http.server
import os
import socketserver
import sys
import urllib.parse
from pathlib import Path

from winout import force_utf8

ROOT = Path(__file__).parent / "fixture"


class Handler(http.server.SimpleHTTPRequestHandler):
    def translate_path(self, path):
        p = urllib.parse.urlparse(path)
        name = p.path.lstrip("/") or "index.html"
        if p.query:
            name = f"{name}__{p.query}"
        return str(ROOT / name)

    def guess_type(self, path):
        # view.html__id=1024 같은 이름 때문에 확장자 추측이 빗나간다
        if ".html" in path:
            return "text/html; charset=utf-8"
        if path.endswith(".css"):
            return "text/css; charset=utf-8"
        return super().guess_type(path)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    force_utf8()
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8731
    os.chdir(ROOT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", port), Handler) as httpd:
        print(f"http://127.0.0.1:{port}/index.html")
        httpd.serve_forever()
