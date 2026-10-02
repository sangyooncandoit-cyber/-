"""공공 웹사이트 불법광고 탐지 도구 — 구동 파일.

더블클릭하면 브라우저에 화면이 열린다. 주소를 넣고 탐지 시작을 누르면
같은 폴더에 result.json 이 만들어진다.

화면을 브라우저로 띄우는 이유
  - 파이썬 기본 라이브러리만 쓰므로 구동 파일이 커지지 않는다.
    접수가 이메일이라 용량이 곧 제출 가능 여부다.
  - 탐지 근거를 보여주고 조치 목록을 내려받는 데 브라우저가 가장 편하다.

적격평가용으로 창 없이 돌릴 수도 있다.
    adguard.exe --url https://example.go.kr --headless
"""
import argparse
import json
import mimetypes
import socket
import sys
import threading
import time
import webbrowser
from urllib.parse import quote
from datetime import datetime, timezone, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from winout import force_utf8

KST = timezone(timedelta(hours=9))
VERSION = "1.0.0"



def base_dir():
    """구동 파일이 놓인 폴더. result.json 은 여기에 만든다."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def asset_dir():
    """화면 파일이 들어있는 곳. PyInstaller 는 _MEIPASS 에 풀어 놓는다."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


class Job:
    """한 번의 탐지. 화면이 진행 상황을 물어볼 수 있게 상태를 들고 있다."""

    def __init__(self):
        self.lock = threading.Lock()
        self.reset()

    def reset(self):
        self.running = False
        self.entry = ""
        self.pages = 0
        self.found = 0
        self.current = ""
        self.started = 0.0
        self.elapsed = 0.0
        self.error = ""
        self.result = None
        self.stats = {}

    def snapshot(self):
        with self.lock:
            return {
                "running": self.running,
                "pages": self.pages,
                "found": self.found,
                "current": self.current,
                "elapsed": (time.monotonic() - self.started) if self.running
                           else self.elapsed,
                "error": self.error,
            }

    def _begin_locked(self, url):
        self.reset()
        self.running = True
        self.entry = url
        self.started = time.monotonic()

    def begin(self, url):
        """스레드를 띄우기 전에 '돌고 있다'를 먼저 세운다.
        작은 사이트는 스레드가 뜨기도 전에 화면이 상태를 물어 와서,
        아직 시작 안 한 것을 '끝났는데 결과가 없다'로 읽어 버린다."""
        with self.lock:
            self._begin_locked(url)

    def run(self, url, outdir, max_pages=None):
        from scan import crawl
        from run import build_result

        with self.lock:
            if not self.running:        # headless 처럼 begin 을 거치지 않은 길
                self._begin_locked(url)
        started_at = datetime.now(KST)

        def progress(n, page, found):
            with self.lock:
                self.pages, self.current, self.found = n, page, found

        try:
            kw = {"max_pages": max_pages} if max_pages else {}
            findings, stats = crawl(url, progress=progress, **kw)
            uniq, seen = [], set()
            for f in findings:
                k = (f["url"], f["location"], f["technique"])
                if k not in seen:
                    seen.add(k)
                    uniq.append(f)
            elapsed = time.monotonic() - self.started
            result = build_result(url, uniq, started_at, datetime.now(KST), elapsed)

            # 공고문 스키마대로만 파일에 쓴다. 화면용 필드는 따로 얹는다.
            (Path(outdir) / "result.json").write_text(
                json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

            extra = {(f["url"], f["location"], f["technique"]): f for f in uniq}
            shown = json.loads(json.dumps(result, ensure_ascii=False))
            for f in shown["findings"]:
                src = extra.get((f["url"], f["location"], f["technique"]), {})
                f["_reason"] = src.get("_reason", "")
                f["_normalized"] = src.get("_normalized", "")
                f["_signals"] = src.get("_signals", [])

            with self.lock:
                self.result = shown
                self.stats = stats
                self.pages = stats["pages"]
                self.found = len(uniq)
                self.elapsed = elapsed
                self.running = False
            return result
        except Exception as ex:                      # noqa: BLE001
            with self.lock:
                self.error = f"탐지 중 문제가 생겼습니다. {type(ex).__name__}: {ex}"
                self.running = False
                self.elapsed = time.monotonic() - self.started
            return None


JOB = Job()
OUTDIR = base_dir()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, body=b"", ctype="application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._file("ui.html", "text/html; charset=utf-8")
        if path == "/app.js":
            return self._file("app.js", "text/javascript; charset=utf-8")
        if path == "/api/status":
            return self._json(JOB.snapshot())
        if path == "/api/result":
            with JOB.lock:
                r = JOB.result
            return self._json(r or {"meta": {}, "findings": []})
        self._send(404, b"not found", "text/plain; charset=utf-8")

    def do_POST(self):
        if self.path != "/api/scan":
            return self._send(404, b"not found", "text/plain; charset=utf-8")
        try:
            n = int(self.headers.get("content-length", 0))
            url = json.loads(self.rfile.read(n) or b"{}").get("url", "").strip()
        except Exception:
            return self._send(400, "요청을 읽지 못했습니다.".encode(), "text/plain; charset=utf-8")
        if not url.lower().startswith(("http://", "https://")):
            return self._send(400, "http 로 시작하는 주소를 넣어 주세요.".encode(),
                              "text/plain; charset=utf-8")
        with JOB.lock:
            if JOB.running:
                return self._send(409, "이미 탐지 중입니다.".encode(),
                                  "text/plain; charset=utf-8")
        JOB.begin(url)
        threading.Thread(target=JOB.run, args=(url, OUTDIR), daemon=True).start()
        self._json({"ok": True})

    def _file(self, name, ctype):
        p = asset_dir() / name
        try:
            self._send(200, p.read_bytes(), ctype)
        except OSError:
            self._send(404, b"missing asset", "text/plain; charset=utf-8")

    def log_message(self, *a):
        pass


def free_port(start=8777):
    for p in range(start, start + 60):
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:
                return p
    return 0


def main():
    force_utf8()
    ap = argparse.ArgumentParser(description="공공 웹사이트 불법광고 탐지 도구")
    ap.add_argument("--url", help="바로 탐지할 진입 주소")
    ap.add_argument("--headless", action="store_true", help="창 없이 돌리고 끝낸다")
    ap.add_argument("--out", default=None, help="result.json 을 만들 폴더")
    ap.add_argument("--max-pages", type=int, default=None,
                    help="살펴볼 페이지 수 상한 (기본 400)")
    args = ap.parse_args()

    global OUTDIR
    OUTDIR = Path(args.out).resolve() if args.out else base_dir()
    OUTDIR.mkdir(parents=True, exist_ok=True)

    if args.headless:
        if not args.url:
            print("--headless 에는 --url 이 필요합니다.")
            return 2
        print(f"탐지 시작 : {args.url}")
        r = JOB.run(args.url, OUTDIR, args.max_pages)
        s = JOB.snapshot()
        if s["error"]:
            print(s["error"])
            return 1
        print(f"페이지 {s['pages']}개 / {s['elapsed']:.1f}초 / 검출 {len(r['findings'])}건")
        bad = JOB.stats.get("failed", [])
        if bad:
            print(f"못 읽은 페이지 {len(bad)}개 — 세 번 시도해도 응답이 없었습니다")
            for u in bad[:5]:
                print(f"  {u}")
        print(f"결과 파일 : {OUTDIR / 'result.json'}")
        return 0

    port = free_port()
    if not port:
        print("쓸 수 있는 포트를 찾지 못했습니다.")
        return 1
    srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = f"http://127.0.0.1:{port}/"
    # --url 만 주고 켰을 때 화면이 그냥 열리고 끝나지 않도록, 주소를 들려 보내
    # 화면이 알아서 탐지를 시작하게 한다.
    open_url = url + ("?url=" + quote(args.url, safe="") if args.url else "")
    print("공공 웹사이트 불법광고 탐지 도구")
    print(f"  화면 주소 : {url}")
    print(f"  결과 파일 : {OUTDIR / 'result.json'}")
    print("  이 창을 닫으면 종료됩니다.")
    try:
        webbrowser.open(open_url)
    except Exception:
        print("  브라우저가 자동으로 열리지 않으면 위 주소를 직접 입력해 주세요.")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("\n종료합니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
