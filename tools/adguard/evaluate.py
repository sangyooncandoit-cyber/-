"""탐지 결과를 정답표와 대조한다.

적격평가와 같은 방식으로 센다.
  정답 검출 개수   — 정답을 몇 개나 찾았나
  정답 추출 정확도 — 신고한 것 중 몇 개가 맞았나 (오탐이 깎는다)

location 은 문자열이 같은지가 아니라 같은 요소를 가리키는지로 본다.
채점 기준이 그렇다. 그래서 실제로 선택자를 돌려 비교한다.
"""
import json
import sys
from pathlib import Path
from urllib.parse import urlparse, urldefrag

import lxml.html
import requests


def page_key(url):
    u, _ = urldefrag(url)
    p = urlparse(u)
    path = p.path.lstrip("/") or "index.html"
    q = "&".join(sorted(p.query.split("&"))) if p.query else ""
    return f"{path}?{q}" if q else path


def resolve(base, location, cache):
    """선택자가 가리키는 요소를 (페이지, 경로) 로 돌려준다.
    iframe 구간은 >>> 로 나뉘어 있다."""
    parts = [s.strip() for s in location.split(">>>")]
    url = base
    for i, seg in enumerate(parts):
        if url not in cache:
            try:
                cache[url] = lxml.html.fromstring(
                    requests.get(url, timeout=10).text)
            except Exception:
                return None
        tree = cache[url]
        if i < len(parts) - 1:
            # iframe[src="..."] 에서 주소를 꺼낸다
            try:
                el = tree.cssselect(seg)[0]
            except Exception:
                return None
            url = el.get("src")
            if not url.startswith("http"):
                from urllib.parse import urljoin
                url = urljoin(base, url)
        else:
            try:
                hits = tree.cssselect(seg)
            except Exception:
                return None
            if len(hits) != 1:
                return None
            return (page_key(url), tree.getroottree().getpath(hits[0]))
    return None


def main(result_path, answers_path, base_root):
    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
    answers = json.loads(Path(answers_path).read_text(encoding="utf-8"))
    cache = {}

    got = set()
    detail = []
    for f in result["findings"]:
        r = resolve(f["url"], f["location"], cache)
        key = (r, f["technique"]) if r else (("?", f["location"]), f["technique"])
        got.add(key)
        detail.append((key, f))

    want = set()
    for a in answers:
        page = a["page"].replace("|iframe", "")
        base = base_root + "/" + (a["page"].split("|")[0] if "|" in a["page"]
                                  else "index.html")
        # 정답은 fixture 기준 페이지 + 선택자로 적혀 있다
        url = base_root + "/" + page.replace("__", "?")
        if "iframe[" in a["location"]:
            url = base_root + "/index.html"
        r = resolve(url, a["location"], cache)
        want.add((r, a["technique"]) if r else ((page, a["location"]), a["technique"]))

    hit = got & want
    missed = want - got
    false_pos = got - want

    print(f"정답 {len(want)}건 / 신고 {len(got)}건")
    print(f"  맞게 찾음 {len(hit)}건")
    print(f"  놓침     {len(missed)}건")
    print(f"  오탐     {len(false_pos)}건")
    recall = len(hit) / len(want) * 100 if want else 0
    prec = len(hit) / len(got) * 100 if got else 0
    print(f"\n  검출률 {recall:.1f}%   정확도 {prec:.1f}%")

    if missed:
        print("\n── 놓친 것 ──")
        for m in sorted(missed, key=str):
            print("  ", m)
    if false_pos:
        print("\n── 잘못 신고한 것 ──")
        for k, f in detail:
            if k in false_pos:
                print(f"   {f['technique']:12s} {f['evidence_text'][:40]!r}")
                print(f"      {f['location']}")
    return len(missed) == 0 and len(false_pos) == 0


if __name__ == "__main__":
    ok = main(sys.argv[1], sys.argv[2], sys.argv[3])
    sys.exit(0 if ok else 1)
