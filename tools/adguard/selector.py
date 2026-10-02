"""검출 위치를 CSS 선택자로 적는다.

공고문 붙임4 규칙을 그대로 따른다.

  - 태그명과 클래스를 함께 적고, 상위 요소부터 " > " 로 연결
      div.notice-board > span.visually-hidden
  - 클래스가 없는 요소는 tr:nth-of-type(7) 처럼 순서로 지정
  - 속성값은 큰따옴표
  - iframe 내부는  iframe[src="주소"] >>> 선택자   형식, 앞뒤 공백 한 칸
    여러 겹이면 >>> 를 반복. src 가 상대경로면 절대주소로 바꿔 적는다

채점은 선택자 문자열이 정답과 같은지가 아니라 같은 요소를 가리키는지로
본다. 다만 두 곳 이상을 가리키면 오답이다. 그래서 만든 선택자가 문서에서
정확히 하나만 잡는지 반드시 검증한다.
"""
from urllib.parse import urljoin

# 굳이 경로에 넣지 않아도 되는 껍데기들
SKIP_TAGS = {"html", "body"}
# 자동 생성처럼 보이는 클래스는 쓰지 않는다 (해시·난수)
import re
NOISY_CLASS = re.compile(r'^(?:[0-9]|.*[0-9a-f]{6,}|.*--[0-9a-z]{4,}$)')


def _useful_classes(el):
    raw = (el.get("class") or "").split()
    return [c for c in raw if c and not NOISY_CLASS.match(c)][:2]


def _step(el):
    """요소 하나를 가리키는 조각. 클래스가 있으면 클래스, 없으면 순서."""
    tag = el.tag if isinstance(el.tag, str) else "node"
    cls = _useful_classes(el)
    if cls:
        return tag + "".join("." + c for c in cls)
    parent = el.getparent()
    if parent is None:
        return tag
    same = [c for c in parent if c.tag == el.tag]
    if len(same) <= 1:
        return tag
    return f"{tag}:nth-of-type({same.index(el) + 1})"


def css_path(el, root=None):
    """요소까지의 선택자 경로를 만든다."""
    parts = []
    cur = el
    while cur is not None and cur is not root:
        tag = cur.tag if isinstance(cur.tag, str) else None
        if tag is None:          # 주석·PI 는 건너뛴다
            cur = cur.getparent()
            continue
        if tag in SKIP_TAGS:
            break
        parts.append(_step(cur))
        cur = cur.getparent()
    return " > ".join(reversed(parts))


def unique_selector(el, tree):
    """하나만 가리킬 때까지 경로를 늘린다.

    짧은 선택자가 읽기 좋지만, 두 곳 이상을 가리키면 오답 처리된다.
    그래서 짧은 것부터 시도하고 중복이면 조상을 한 단계씩 더 붙인다.
    """
    chain = []
    cur = el
    while cur is not None:
        tag = cur.tag if isinstance(cur.tag, str) else None
        if tag is None or tag in SKIP_TAGS:
            break
        chain.append(cur)
        cur = cur.getparent()

    for depth in range(1, len(chain) + 1):
        sel = " > ".join(_step(n) for n in reversed(chain[:depth]))
        try:
            hits = tree.cssselect(sel)
        except Exception:
            continue
        if len(hits) == 1 and hits[0] is el:
            return sel
    # 끝까지 못 좁히면 클래스는 그대로 두고 순서를 덧붙인다.
    # 클래스를 버리면 선택자가 읽기 어려워지고, 문서가 조금만 달라져도
    # 엉뚱한 곳을 가리키게 된다.
    parts = []
    for n in reversed(chain):
        tag = n.tag
        cls = _useful_classes(n)
        base = tag + "".join("." + c for c in cls)
        parent = n.getparent()
        if parent is not None:
            same_tag = [c for c in parent if c.tag == tag]
            twins = [c for c in same_tag if _useful_classes(c) == cls]
            if len(twins) > 1:
                base += f":nth-of-type({same_tag.index(n) + 1})"
        parts.append(base)
    return " > ".join(parts)


def iframe_prefix(frame_srcs, page_url):
    """iframe 안쪽 요소 앞에 붙일 경로.

    iframe[src="절대주소"] >>> ... 형식. 중첩이면 >>> 를 반복한다.
    """
    parts = []
    for src in frame_srcs:
        absolute = urljoin(page_url, src)
        parts.append(f'iframe[src="{absolute}"]')
    return " >>> ".join(parts)


def full_location(el, tree, frame_srcs=(), page_url=""):
    """최종 location 문자열."""
    sel = unique_selector(el, tree)
    if not frame_srcs:
        return sel
    return iframe_prefix(frame_srcs, page_url) + " >>> " + sel
