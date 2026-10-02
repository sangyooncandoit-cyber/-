"""아주 작은 CSS 캐스케이드.

투명 텍스트와 화면 밖 은닉은 '계산된 스타일'을 봐야 잡힌다.
브라우저를 통째로 넣으면 정확하지만 exe 가 200MB 를 넘어 메일로 못 보내고,
무엇보다 느려서 검출 시간 20점에서 깎인다.

그래서 필요한 속성만 직접 계산한다. 전부 구현할 필요가 없다 —
숨기는 데 쓰이는 속성은 열 개 남짓이다.

우선순위는 CSS 명세대로. inline > id > class > tag, 같으면 나중 것.
"""
import re
from urllib.parse import urljoin

import tinycss2
from lxml import etree

# 숨김과 관계있는 속성만 본다. 나머지는 계산할 이유가 없다.
WATCH = {
    "color", "background-color", "background", "opacity", "visibility",
    "display", "position", "left", "top", "right", "bottom",
    "font-size", "text-indent", "width", "height", "overflow",
    "clip", "clip-path", "transform", "z-index", "line-height",
}
# 자식에게 물려주는 속성
INHERITED = {"color", "visibility", "font-size", "line-height", "text-indent"}

AT_RULE_SKIP = {"media", "supports", "layer", "container"}


def _specificity(sel):
    """(id 개수, class/속성/가상클래스 개수, 태그 개수)."""
    s = re.sub(r'\[[^\]]*\]', '[]', sel)
    ids = s.count('#')
    cls = s.count('.') + s.count('[') + len(re.findall(r'(?<!:):(?!:)[a-z-]+', s))
    tags = len(re.findall(r'(?:^|[\s>+~])([a-zA-Z][\w-]*)', s))
    return (ids, cls, tags)


def parse_stylesheet(css_text):
    """(선택자, {속성: 값}, 중요도, 등장순서) 목록."""
    out = []
    try:
        rules = tinycss2.parse_stylesheet(css_text, skip_comments=True,
                                          skip_whitespace=True)
    except Exception:
        return out
    order = 0

    def handle(rule_list):
        nonlocal order
        for rule in rule_list:
            if rule.type == "at-rule":
                # @media 등은 조건을 따지지 않고 내용만 꺼낸다.
                # 숨김 목적 CSS 가 미디어쿼리 안에 들어있는 경우를 놓치지 않으려는 것.
                if rule.lower_at_keyword in AT_RULE_SKIP and rule.content:
                    try:
                        handle(tinycss2.parse_rule_list(
                            rule.content, skip_comments=True, skip_whitespace=True))
                    except Exception:
                        pass
                continue
            if rule.type != "qualified-rule":
                continue
            prelude = tinycss2.serialize(rule.prelude).strip()
            decls = {}
            important = set()
            for d in tinycss2.parse_blocks_contents(rule.content):
                if d.type != "declaration":
                    continue
                name = d.lower_name
                if name not in WATCH:
                    continue
                decls[name] = tinycss2.serialize(d.value).strip()
                if d.important:
                    important.add(name)
            if not decls:
                continue
            for sel in prelude.split(","):
                sel = sel.strip()
                if sel:
                    out.append((sel, decls, important, order))
                    order += 1

    handle(rules)
    return out


def parse_inline(style_attr):
    decls, important = {}, set()
    if not style_attr:
        return decls, important
    try:
        for d in tinycss2.parse_blocks_contents(style_attr):
            if d.type == "declaration" and d.lower_name in WATCH:
                decls[d.lower_name] = tinycss2.serialize(d.value).strip()
                if d.important:
                    important.add(d.lower_name)
    except Exception:
        pass
    return decls, important


class Cascade:
    """문서 하나에 대한 계산된 스타일 제공자."""

    def __init__(self, tree, css_sources):
        self.tree = tree
        self.rules = []
        for text in css_sources:
            self.rules.extend(parse_stylesheet(text))
        self._matched = {}          # 요소 -> [(우선순위, decls, important)]
        self._computed = {}
        self._build()

    def _build(self):
        for sel, decls, important, order in self.rules:
            try:
                targets = self.tree.cssselect(sel)
            except Exception:
                continue            # 지원 못 하는 선택자는 건너뛴다
            spec = _specificity(sel)
            for el in targets:
                self._matched.setdefault(el, []).append(
                    (spec, order, decls, important))

    def computed(self, el):
        """요소의 계산된 스타일. 상속도 반영한다."""
        if el in self._computed:
            return self._computed[el]

        parent = el.getparent()
        style = {}
        if parent is not None and isinstance(parent.tag, str):
            pstyle = self.computed(parent)
            style = {k: v for k, v in pstyle.items() if k in INHERITED}

        own = {}
        imp = {}
        for spec, order, decls, important in sorted(
                self._matched.get(el, []), key=lambda r: (r[0], r[1])):
            for k, v in decls.items():
                if k in important:
                    imp[k] = v
                else:
                    own[k] = v

        inline, inline_imp = parse_inline(el.get("style"))
        own.update(inline)
        for k in inline_imp:
            imp[k] = inline[k]
        own.update(imp)             # !important 가 마지막

        style.update(own)
        self._computed[el] = style
        return style

    def effective_background(self, el):
        """조상을 거슬러 올라가며 실제 배경색을 찾는다.
        배경이 지정되지 않으면 흰색으로 본다."""
        from detect import parse_color
        cur = el
        while cur is not None and isinstance(cur.tag, str):
            st = self.computed(cur)
            for key in ("background-color", "background"):
                c = parse_color(st.get(key))
                if c and c[3] > 0.5:
                    return c
            cur = cur.getparent()
        return (255, 255, 255, 1.0)


def collect_css(tree, base_url, fetch):
    """문서가 쓰는 CSS 를 모은다. <style> 과 외부 파일."""
    sources = []
    for st in tree.cssselect("style"):
        if st.text:
            sources.append(st.text)
    for link in tree.cssselect('link[rel~="stylesheet"], link[href$=".css"]'):
        href = link.get("href")
        if not href:
            continue
        text = fetch(urljoin(base_url, href))
        if text:
            sources.append(text)
    return sources
