"""result.json 이 공고문 붙임4 요건을 지켰는지 본다.

스키마를 어기면 그 항목은 채점에서 빠지고, 파일 전체가 파싱 안 되면 0점이다.
정답을 몇 개 찾았는지보다 먼저 통과해야 하는 관문이라 따로 둔다.

  python verify_result.py result.json
  python verify_result.py result_extra.json --extra
"""
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse, urldefrag

TECHNIQUES = {"HOMOGLYPH", "JAMO", "TRANSPARENT", "OFFSCREEN"}
META_REQUIRED = {"topic", "entry_url", "started_at", "finished_at", "elapsed_sec"}
META_ALLOWED = META_REQUIRED | {"tool_version"}
FINDING_REQUIRED = ["id", "url", "is_violation", "location", "evidence_text", "technique"]
TIMEOUT_SEC = 30 * 60          # 상한 30분. 넘기면 검출 시간 20점이 0점이다.


def force_utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass


def norm_url(u):
    """채점이 같은 페이지로 보는 기준에 맞춰 줄인다.
    끝의 / 와 http/https 차이와 # 뒤는 안 본다. 쿼리는 순서만 다르면 같다."""
    u, _ = urldefrag(u or "")
    p = urlparse(u)
    host = (p.hostname or "").lower()
    if p.port:
        host += f":{p.port}"
    path = p.path.rstrip("/") or "/"
    query = "&".join(sorted(x for x in p.query.split("&") if x))
    return f"{host}{path}" + (f"?{query}" if query else "")


def check_iso(v):
    try:
        datetime.fromisoformat(v)
        return True
    except (TypeError, ValueError):
        return False


def verify(path, extra=False):
    errs, warns = [], []
    p = Path(path)

    raw = p.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errs.append("파일 앞에 BOM 이 붙어 있다. 붙임4 는 'UTF-8(BOM 없음)' 이다.")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as ex:
        errs.append(f"UTF-8 로 읽히지 않는다. {ex}")
        return errs, warns, None
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as ex:
        errs.append(f"JSON 파싱 실패. 파일 전체가 0점 처리된다. {ex}")
        return errs, warns, None

    if not isinstance(doc, dict):
        errs.append("최상위가 객체가 아니다.")
        return errs, warns, None

    # ── 최상위
    top = set(doc)
    if top != {"meta", "findings"}:
        errs.append(f"최상위는 meta 와 findings 두 개여야 한다. 지금: {sorted(top)}")
    if "findings" not in doc:
        errs.append("검출이 없어도 findings 는 빈 배열로 있어야 한다.")
        return errs, warns, None
    if not isinstance(doc["findings"], list):
        errs.append("findings 는 배열이어야 한다.")
        return errs, warns, None

    # ── meta
    meta = doc.get("meta")
    if not isinstance(meta, dict):
        errs.append("meta 가 객체가 아니다.")
        meta = {}
    for k in sorted(META_REQUIRED - set(meta)):
        errs.append(f"meta.{k} 가 없다. (필수)")
    for k in sorted(set(meta) - META_ALLOWED):
        warns.append(f"meta.{k} 는 규정에 없는 필드다.")
    if "topic" in meta and meta["topic"] != "TOPIC":
        warns.append(f'meta.topic 이 "TOPIC" 이 아니다: {meta["topic"]!r}')
    for k in ("started_at", "finished_at"):
        if k in meta and not check_iso(meta[k]):
            errs.append(f"meta.{k} 가 ISO 8601 이 아니다: {meta[k]!r}")
    sec = meta.get("elapsed_sec")
    if "elapsed_sec" in meta and not isinstance(sec, (int, float)):
        errs.append(f"meta.elapsed_sec 는 숫자여야 한다: {sec!r}")
    elif isinstance(sec, (int, float)) and sec > TIMEOUT_SEC:
        errs.append(f"소요 시간 {sec:.0f}초. 상한 30분(1800초)을 넘겨 검출 시간 0점이다.")
    if not isinstance(meta.get("entry_url", ""), str) or not meta.get("entry_url"):
        errs.append("meta.entry_url 이 비어 있다.")

    # ── findings
    allowed = set(FINDING_REQUIRED) | ({"extra_finding"} if extra else set())
    ids, combos = set(), {}
    for i, f in enumerate(doc["findings"]):
        tag = f"findings[{i}]"
        if not isinstance(f, dict):
            errs.append(f"{tag} 가 객체가 아니다.")
            continue
        for k in FINDING_REQUIRED:
            if k not in f:
                errs.append(f"{tag}.{k} 가 없다. 이 항목은 채점에서 빠진다.")
        for k in sorted(set(f) - allowed):
            errs.append(f"{tag}.{k} 는 규정에 없는 필드다. 스키마 미준수로 오답 처리된다.")

        fid = f.get("id")
        if not isinstance(fid, str) or not fid:
            errs.append(f"{tag}.id 가 비었거나 문자열이 아니다.")
        elif fid in ids:
            errs.append(f"{tag}.id 가 파일 안에서 중복이다: {fid}")
        else:
            ids.add(fid)

        if not isinstance(f.get("is_violation"), bool):
            errs.append(f"{tag}.is_violation 은 참·거짓이어야 한다: "
                        f"{f.get('is_violation')!r}")

        t = f.get("technique")
        want = TECHNIQUES | {"ETC"} if extra else TECHNIQUES
        if isinstance(t, list):
            errs.append(f"{tag}.technique 에 배열을 쓸 수 없다. 기법마다 객체를 따로 만든다.")
        elif not isinstance(t, str):
            errs.append(f"{tag}.technique 가 문자열이 아니다: {t!r}")
        elif re.search(r"[,/|]| and | & ", t):
            errs.append(f"{tag}.technique 에 두 개 이상을 나열할 수 없다: {t!r}")
        elif t not in want:
            errs.append(f"{tag}.technique 가 허용 코드가 아니다: {t!r} (허용 {sorted(want)})")
        if extra and t == "ETC" and not f.get("extra_finding"):
            errs.append(f"{tag} 는 ETC 인데 extra_finding 이 비어 있다.")

        loc = f.get("location")
        if not isinstance(loc, str) or not loc.strip():
            errs.append(f"{tag}.location 이 비어 있다.")
        elif ">>>" in loc:
            if re.search(r"\S>>>|>>>\S", loc):
                errs.append(f"{tag}.location 의 >>> 앞뒤에 공백 한 칸이 있어야 한다: {loc}")
            m = re.match(r'\s*iframe\[src="([^"]+)"\]', loc)
            if not m:
                errs.append(f'{tag}.location 의 iframe 은 iframe[src="주소"] 형식이어야 한다: {loc}')
            elif not urlparse(m.group(1)).scheme:
                errs.append(f"{tag}.location 의 iframe src 가 절대 주소가 아니다: {m.group(1)}")

        if not isinstance(f.get("evidence_text"), str) or not f.get("evidence_text"):
            errs.append(f"{tag}.evidence_text 가 비어 있다. 본심사 참고자료라 필수다.")

        if isinstance(f.get("url"), str) and isinstance(loc, str) and isinstance(t, str):
            key = (norm_url(f["url"]), loc, t)
            if key in combos:
                errs.append(f"{tag} 가 {combos[key]} 와 (url+location+technique) 가 같다. "
                            f"중복 검출이다.")
            else:
                combos[key] = tag

    return errs, warns, doc


def main():
    force_utf8()
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    extra = "--extra" in sys.argv
    if not args:
        print("사용법: verify_result.py <result.json> [--extra]")
        return 2

    path = Path(args[0])
    if not path.exists():
        print(f"파일이 없다: {path}")
        return 1

    errs, warns, doc = verify(path, extra)
    print(f"검사 대상 : {path}  ({path.stat().st_size:,} 바이트)")
    if doc:
        m = doc.get("meta", {})
        print(f"  진입 주소 : {m.get('entry_url', '?')}")
        print(f"  소요 시간 : {m.get('elapsed_sec', '?')}초")
        print(f"  검출 건수 : {len(doc.get('findings', []))}건")
        by = {}
        for f in doc.get("findings", []):
            t = f.get("technique")
            if isinstance(t, str):
                by[t] = by.get(t, 0) + 1
        if by:
            print("  유형별    : " + ", ".join(f"{k} {v}" for k, v in sorted(by.items())))

    for w in warns:
        print(f"  [참고] {w}")
    if errs:
        print(f"\n스키마 위반 {len(errs)}건")
        for e in errs:
            print(f"  [오류] {e}")
        return 1
    print("\n스키마 통과. 붙임4 요건을 모두 만족한다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
