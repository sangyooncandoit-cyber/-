"""공공 웹사이트 불법광고 탐지 — 수집과 판정.

진입 URL 하나를 받아 같은 사이트의 하위 페이지, 게시글, 댓글 영역,
iframe 내부까지 훑는다.

검출 1건의 단위는 (url + location + technique) 조합이다.
같은 요소에 기법이 둘이면 각각 1건으로 센다. 공고문 붙임4 규칙이다.
"""
import concurrent.futures as cf
import time
from collections import deque
from urllib.parse import urljoin, urlparse, urldefrag

import lxml.html
import requests

from cascade import Cascade, collect_css
from detect import find_homoglyph, find_jamo, find_transparent, find_offscreen
from lexicon import looks_like_ad
from selector import full_location

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")
SKIP_EXT = (".pdf", ".hwp", ".hwpx", ".zip", ".jpg", ".jpeg", ".png", ".gif",
            ".xls", ".xlsx", ".doc", ".docx", ".ppt", ".pptx", ".mp4", ".svg")
# 텍스트를 들고 있을 수 없는 태그
NO_TEXT = {"script", "style", "noscript", "head", "meta", "link", "title"}


def norm_url(u):
    """채점 기준에 맞춰 URL 을 정규화한다.
    끝의 / 유무, http/https 차이, # 뒤는 비교하지 않는다.
    ? 뒤 쿼리는 값이 다르면 다른 페이지로 본다. 순서만 다르면 같은 페이지."""
    u, _ = urldefrag(u)
    p = urlparse(u)
    path = p.path.rstrip("/") or "/"
    q = "&".join(sorted(p.query.split("&"))) if p.query else ""
    return f"{p.netloc.lower()}{path}" + (f"?{q}" if q else "")


class Fetcher:
    # 한 번 실패했다고 버리면 그 페이지의 검출 건이 통째로 날아간다.
    # 네트워크가 한 번 끊기는 것과 그 페이지에 광고가 없는 것은 다른 일이다.
    RETRY_ON = (429, 500, 502, 503, 504)
    BACKOFF = (0.5, 1.5)          # 두 번까지 더 해 본다

    def __init__(self, timeout=12):
        self.s = requests.Session()
        self.s.headers["User-Agent"] = UA
        self.timeout = timeout
        self.css_cache = {}
        self.failed = []          # 끝내 못 읽은 주소. 결과 화면에 알려 준다
        self.retried = 0

    def _once(self, url):
        """(본문, 최종주소, 다시 해 볼 만한가)"""
        try:
            r = self.s.get(url, timeout=self.timeout, allow_redirects=True)
        except Exception:
            return None, None, True                   # 끊김·시간초과 — 다시
        if r.status_code in self.RETRY_ON:
            return None, None, True
        if r.status_code != 200:
            return None, None, False                  # 404 같은 것은 그만
        try:
            r.encoding = r.apparent_encoding or r.encoding
            text = r.text
        except Exception:
            return None, None, False
        ct = r.headers.get("content-type", "").lower()
        if "html" in ct or "xml" in ct or not ct:
            return text, str(r.url), False
        # 서버가 엉뚱한 content-type 을 주는 경우가 있다. 게시판 주소에
        # 확장자가 없거나 쿼리가 붙으면 octet-stream 으로 내려오기도 한다.
        # 그때 그냥 버리면 페이지를 통째로 놓치므로 본문을 보고 판단한다.
        head = text[:4096].lstrip().lower()
        if head.startswith(("<!doctype html", "<html", "<?xml")) or "<body" in head:
            return text, str(r.url), False
        return None, None, False                      # 그림·PDF 같은 것

    def get(self, url):
        for i, wait in enumerate((0.0,) + self.BACKOFF):
            if wait:
                time.sleep(wait)
                self.retried += 1
            text, final, again = self._once(url)
            if text is not None:
                return text, final
            if not again:
                return None, None
        self.failed.append(url)
        return None, None

    def css(self, url):
        if url in self.css_cache:
            return self.css_cache[url]
        try:
            r = self.s.get(url, timeout=self.timeout)
            text = r.text if r.status_code == 200 else ""
        except Exception:
            text = ""
        self.css_cache[url] = text
        return text


def own_text(el):
    """자식 것 말고 이 요소가 직접 들고 있는 글."""
    parts = [el.text or ""]
    for child in el:
        parts.append(child.tail or "")
    return "".join(parts).strip()


def analyse_document(html, page_url, fetcher, frame_srcs=(), host_url=None):
    """문서 하나를 보고 (검출목록, 따라갈 링크, iframe 주소) 를 돌려준다.

    host_url 은 검출 결과에 적을 페이지 주소다. iframe 안을 볼 때는
    iframe 문서가 아니라 그것을 품은 바깥 페이지 주소를 적어야 한다."""
    report_url = host_url or page_url
    try:
        tree = lxml.html.fromstring(html)
    except Exception:
        return [], [], []
    tree.make_links_absolute(page_url, resolve_base_href=True)

    # 스타일시트 받아오기와 캐스케이드 만들기를 둘 다 미룬다.
    # 실제로 필요한 페이지에서만 값을 치른다.
    cas = Cascade(tree, lambda: collect_css(tree, page_url, fetcher.css))

    findings = []
    for el in tree.iter():
        if not isinstance(el.tag, str) or el.tag in NO_TEXT:
            continue
        text = own_text(el)
        if not text:
            continue

        techniques = []

        # 1·2. 글자 자체를 비튼 경우 — 숨어 있지 않아도 그 자체가 회피 행위다
        if (hg := find_homoglyph(text)):
            norm, scripts = hg
            ok, hits = looks_like_ad(norm, threshold=1)
            if ok:
                techniques.append(("HOMOGLYPH", text, {
                    "reason": f"{', '.join(scripts)} 문자를 섞어 필터를 피함",
                    "normalized": norm,
                    "signals": hits,
                }))
        if (jm := find_jamo(text)):
            ok, hits = looks_like_ad(jm, threshold=1)
            if ok:
                techniques.append(("JAMO", text, {
                    "reason": "음절을 자모로 쪼개 키워드 매칭을 우회함",
                    "normalized": jm,
                    "signals": hits,
                }))

        # 3·4. 숨긴 경우 — 광고처럼 보일 때만 신고한다 (오탐은 정확도 35점을 깎는다)
        #
        # 순서가 중요하다. 두 조건을 모두 만족해야 신고하므로 결과는 같은데,
        # 스타일 계산이 글자 검사보다 수십 배 비싸다. 멀쩡한 페이지에서는
        # 이 문을 통과하는 요소가 거의 없어서 캐스케이드를 아예 안 만들게 된다.
        probe = text
        if (hg2 := find_homoglyph(text)):
            probe = hg2[0]
        if (jm2 := find_jamo(probe)):
            probe = jm2
        ok, hits = looks_like_ad(probe, threshold=2)
        if ok:
            style = cas.computed(el)
            bg = cas.effective_background(el)
            trans = find_transparent(style, bg)
            off = find_offscreen(style)
            extra = {"normalized": probe if probe != text else "",
                     "signals": hits}
            if trans:
                techniques.append(("TRANSPARENT", text,
                                   dict(extra, reason=trans)))
            if off:
                techniques.append(("OFFSCREEN", text,
                                   dict(extra, reason=off)))

        if techniques:
            loc = full_location(el, tree, frame_srcs, report_url)
            for tech, evidence, extra in techniques:
                findings.append({
                    "url": report_url,
                    "is_violation": True,
                    "location": loc,
                    "evidence_text": evidence,
                    "technique": tech,
                    # 아래는 화면 전용. result.json 에는 나가지 않는다.
                    "_reason": extra.get("reason", ""),
                    "_normalized": extra.get("normalized", ""),
                    "_signals": extra.get("signals", []),
                    "_tag": el.tag,
                })

    host = urlparse(page_url).netloc.lower()
    links = []
    for a in tree.cssselect("a[href]"):
        href = a.get("href") or ""
        if href.lower().startswith(("javascript:", "mailto:", "tel:")):
            continue
        u, _ = urldefrag(urljoin(page_url, href))
        if urlparse(u).netloc.lower() != host:
            continue
        if u.lower().endswith(SKIP_EXT):
            continue
        links.append(u)

    frames = []
    for f in tree.cssselect("iframe[src], frame[src]"):
        src = f.get("src") or ""
        if src and not src.lower().startswith(("javascript:", "about:")):
            frames.append(src)
    return findings, links, frames


def crawl(entry_url, max_pages=400, time_budget=25 * 60, workers=8,
          progress=None):
    """진입 URL 에서 시작해 훑는다. 검출 목록과 통계를 돌려준다."""
    started = time.monotonic()
    fetcher = Fetcher()
    seen = {norm_url(entry_url)}
    queue = deque([(entry_url, (), None)])   # (url, iframe 경로, 바깥 페이지)
    findings = []
    pages = 0

    with cf.ThreadPoolExecutor(max_workers=workers) as pool:
        while queue:
            if time.monotonic() - started > time_budget or pages >= max_pages:
                break
            batch = []
            while queue and len(batch) < workers:
                batch.append(queue.popleft())

            futures = {pool.submit(fetcher.get, u): (u, fr, hu)
                       for u, fr, hu in batch}
            for fut in cf.as_completed(futures):
                url, frames_path, host_url = futures[fut]
                html, final = fut.result()
                if not html:
                    continue
                pages += 1
                if progress:
                    progress(pages, final or url, len(findings))
                f, links, frames = analyse_document(
                    html, final or url, fetcher, frames_path, host_url)
                findings.extend(f)
                # iframe 안에서는 링크를 따라가지 않는다. 바깥 페이지 기준으로
                # 이미 훑고 있어서 중복이 된다.
                if not frames_path:
                    for link in links:
                        k = norm_url(link)
                        if k not in seen:
                            seen.add(k)
                            queue.append((link, (), None))
                # 이 문서가 품은 iframe. 결과에 적을 주소는 바깥 페이지 것을 넘긴다.
                outer = host_url or (final or url)
                for src in frames:
                    absolute = urljoin(final or url, src)
                    k = norm_url(absolute) + "|frame|" + norm_url(outer)
                    if k not in seen:
                        seen.add(k)
                        queue.append((absolute, frames_path + (src,), outer))

    return findings, {
        "pages": pages,
        "elapsed": time.monotonic() - started,
        "queued_left": len(queue),
        "failed": list(fetcher.failed),
        "retried": fetcher.retried,
    }
