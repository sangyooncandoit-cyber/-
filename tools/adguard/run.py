"""명령줄에서 한 번 돌려 result.json 을 만든다."""
import json
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

from winout import force_utf8

sys.path.insert(0, str(Path(__file__).parent))
from scan import crawl                                      # noqa: E402

KST = timezone(timedelta(hours=9))



def build_result(entry_url, findings, started_at, finished_at, elapsed):
    for i, f in enumerate(findings, 1):
        f["id"] = f"f_{i:03d}"
    order = ["id", "url", "is_violation", "location", "evidence_text", "technique"]
    return {
        "meta": {
            "topic": "TOPIC",
            "entry_url": entry_url,
            "started_at": started_at.isoformat(),
            "finished_at": finished_at.isoformat(),
            "elapsed_sec": round(elapsed, 1),
            "tool_version": "1.0.0",
        },
        "findings": [{k: f[k] for k in order} for f in findings],
    }


def main():
    force_utf8()
    if len(sys.argv) < 2:
        print("사용법: run.py <진입 URL> [출력 폴더]")
        return 2
    entry = sys.argv[1]
    outdir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path.cwd()

    started = datetime.now(KST)
    t0 = time.monotonic()

    def progress(n, url, found):
        print(f"  [{n:3d}] {url[:70]:72s} 누적 {found}건")

    findings, stats = crawl(entry, progress=progress)
    elapsed = time.monotonic() - t0
    finished = datetime.now(KST)

    # (url + location + technique) 가 같으면 1건으로 합친다 — 공고문 규칙
    uniq, seen = [], set()
    for f in findings:
        k = (f["url"], f["location"], f["technique"])
        if k not in seen:
            seen.add(k)
            uniq.append(f)

    result = build_result(entry, uniq, started, finished, elapsed)
    out = outdir / "result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n페이지 {stats['pages']}개 / {elapsed:.1f}초 / 검출 {len(uniq)}건")
    print(f"결과 파일: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
