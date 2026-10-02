"""불법광고 은닉 기법 탐지 — 네 가지 유형.

공고문 붙임1 의 '주요 탐지 유형' 4종이 적격평가 대상이다.
네 개 다 규칙으로 정확히 풀린다. AI 를 태울 이유가 없고, 태우면
검출 시간(20점)에서 손해다.

  HOMOGLYPH    키릴·전각 등 닮은꼴 글자를 섞어 필터를 피하는 기법
  JAMO         음절을 자모로 쪼개 키워드 매칭을 우회하는 기법
  TRANSPARENT  배경색과 같은 색, opacity:0, color:transparent
  OFFSCREEN    font-size:0~1px, left:-9999px, display:none
"""
import re
import unicodedata

# ── 1. 닮은꼴 글자 ────────────────────────────────────────────
# 전각(Fullwidth)·키릴·그리스에서 라틴/숫자로 보이는 것들.
# unicodedata.normalize('NFKC') 가 전각은 처리하지만 키릴은 못 한다.
CYRILLIC_TO_LATIN = {
    'А': 'A', 'В': 'B', 'Е': 'E', 'К': 'K', 'М': 'M', 'Н': 'H', 'О': 'O',
    'Р': 'P', 'С': 'C', 'Т': 'T', 'У': 'Y', 'Х': 'X', 'Ѕ': 'S', 'І': 'I',
    'Ј': 'J', 'а': 'a', 'е': 'e', 'о': 'o', 'р': 'p', 'с': 'c', 'у': 'y',
    'х': 'x', 'ѕ': 's', 'і': 'i', 'ј': 'j', 'ԁ': 'd', 'ɡ': 'g', 'һ': 'h',
}
GREEK_TO_LATIN = {
    'Α': 'A', 'Β': 'B', 'Ε': 'E', 'Ζ': 'Z', 'Η': 'H', 'Ι': 'I', 'Κ': 'K',
    'Μ': 'M', 'Ν': 'N', 'Ο': 'O', 'Ρ': 'P', 'Τ': 'T', 'Υ': 'Y', 'Χ': 'X',
    'ο': 'o', 'ν': 'v', 'ρ': 'p', 'τ': 't',
}
CONFUSABLES = {**CYRILLIC_TO_LATIN, **GREEK_TO_LATIN}

# 섞이면 의심스러운 스크립트. 한글+라틴은 정상 조합이라 세지 않는다.
SUSPECT_RANGES = [
    (0x0400, 0x04FF, 'CYRILLIC'),
    (0x0370, 0x03FF, 'GREEK'),
    (0xFF01, 0xFF5E, 'FULLWIDTH'),
    (0x2460, 0x24FF, 'ENCLOSED'),
    (0x1D400, 0x1D7FF, 'MATH_ALNUM'),
]


def script_of(ch):
    cp = ord(ch)
    for lo, hi, name in SUSPECT_RANGES:
        if lo <= cp <= hi:
            return name
    return None


def normalize_confusables(text):
    """닮은꼴을 일반 글자로 되돌린다."""
    t = "".join(CONFUSABLES.get(c, c) for c in text)
    return unicodedata.normalize("NFKC", t)


def find_homoglyph(text):
    """의심 스크립트 글자가 섞여 있으면 (정규화 결과, 쓰인 스크립트들)."""
    scripts = {s for c in text if (s := script_of(c))}
    if not scripts:
        return None
    norm = normalize_confusables(text)
    if norm == text:
        return None
    return norm, sorted(scripts)


# ── 2. 자모 분해 ──────────────────────────────────────────────
CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = "\u0000ㄱㄲㄳㄴㄵㄶㄷㄹㄺㄻㄼㄽㄾㄿㅀㅁㅂㅄㅅㅆㅇㅈㅊㅋㅌㅍㅎ"
# 호환 자모 영역 (U+3131~U+318E) — 낱자로 쓰인 한글
COMPAT_JAMO = re.compile(r'[ㄱ-ㆎ]')


def compose_jamo(text):
    """떨어진 자모를 음절로 되붙인다. ㅋㅏㅈㅣㄴㅗ -> 카지노"""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        ci = CHO.find(c)
        if ci >= 0 and i + 1 < n and (vi := JUNG.find(text[i + 1])) >= 0:
            ti, step = 0, 2
            if i + 2 < n:
                t = JONG.find(text[i + 2])
                # 다음 글자가 또 초성+중성이면 받침이 아니라 다음 음절의 초성이다
                nxt_is_cho = (i + 3 < n and CHO.find(text[i + 2]) >= 0
                              and JUNG.find(text[i + 3]) >= 0)
                if t > 0 and not nxt_is_cho:
                    ti, step = t, 3
            out.append(chr(0xAC00 + (ci * 21 + vi) * 28 + ti))
            i += step
        else:
            out.append(c)
            i += 1
    return "".join(out)


def find_jamo(text):
    """낱자 한글이 2개 이상 연달아 있고, 합치면 글자가 되면 잡는다."""
    if len(COMPAT_JAMO.findall(text)) < 2:
        return None
    composed = compose_jamo(text)
    if composed == text:
        return None
    # 합친 뒤 낱자가 눈에 띄게 줄어야 진짜 분해다
    if len(COMPAT_JAMO.findall(composed)) >= len(COMPAT_JAMO.findall(text)):
        return None
    return composed


# ── 3·4. CSS 로 숨기기 ────────────────────────────────────────
HEX = re.compile(r'#([0-9a-fA-F]{3,8})\b')
RGB = re.compile(r'rgba?\(\s*([\d.]+)\s*[, ]\s*([\d.]+)\s*[, ]\s*([\d.]+)'
                 r'(?:\s*[,/]\s*([\d.%]+))?\s*\)')
NAMED = {
    'white': (255, 255, 255), 'black': (0, 0, 0), 'red': (255, 0, 0),
    'transparent': None, 'whitesmoke': (245, 245, 245), 'snow': (255, 250, 250),
    'ivory': (255, 255, 240), 'azure': (240, 255, 255), 'mintcream': (245, 255, 250),
    'ghostwhite': (248, 248, 255), 'floralwhite': (255, 250, 240),
}
LEN_PX = re.compile(r'(-?[\d.]+)\s*(px|pt|em|rem|%)?')


def parse_color(v):
    """CSS 색을 (r,g,b,a) 로. 못 읽으면 None."""
    if not v:
        return None
    v = v.strip().lower()
    if v in ('transparent',):
        return (0, 0, 0, 0.0)
    if v in NAMED and NAMED[v]:
        r, g, b = NAMED[v]
        return (r, g, b, 1.0)
    if m := HEX.search(v):
        h = m.group(1)
        if len(h) in (3, 4):
            h = "".join(c * 2 for c in h)
        if len(h) in (6, 8):
            r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
            a = int(h[6:8], 16) / 255 if len(h) == 8 else 1.0
            return (r, g, b, a)
    if m := RGB.search(v):
        r, g, b = (int(float(m.group(i))) for i in (1, 2, 3))
        a = m.group(4)
        a = (float(a.rstrip('%')) / 100 if a and a.endswith('%')
             else float(a) if a else 1.0)
        return (r, g, b, a)
    return None


def to_px(v, base=16.0):
    """길이값을 px 로. 못 읽으면 None."""
    if not v:
        return None
    m = LEN_PX.search(v.strip())
    if not m:
        return None
    n = float(m.group(1))
    unit = m.group(2) or 'px'
    return {'px': n, 'pt': n * 4 / 3, 'em': n * base, 'rem': n * base,
            '%': n * base / 100}.get(unit)


def color_distance(a, b):
    return sum(abs(x - y) for x, y in zip(a[:3], b[:3]))


def find_transparent(style, bg=(255, 255, 255, 1.0)):
    """투명 텍스트. 사유를 문자열로 돌려준다."""
    reasons = []
    if (o := style.get('opacity')) is not None:
        try:
            if float(o) <= 0.05:
                reasons.append(f"opacity:{o}")
        except ValueError:
            pass
    col = parse_color(style.get('color'))
    if col:
        if col[3] <= 0.05:
            reasons.append(f"color:{style['color']} (알파 {col[3]})")
        else:
            own_bg = parse_color(style.get('background-color')) or \
                     parse_color(style.get('background'))
            ref = own_bg if (own_bg and own_bg[3] > 0.5) else bg
            if color_distance(col, ref) <= 12:
                reasons.append(f"글자색이 배경색과 같음 ({style['color']})")
    if style.get('visibility', '').strip() == 'hidden':
        reasons.append("visibility:hidden")
    return " / ".join(reasons) or None


def find_offscreen(style):
    """화면 밖 은닉. 사유를 문자열로."""
    reasons = []
    if (fs := to_px(style.get('font-size'))) is not None and fs <= 1.0:
        reasons.append(f"font-size:{style['font-size']}")
    if style.get('display', '').strip() == 'none':
        reasons.append("display:none")
    pos = style.get('position', '').strip()
    if pos in ('absolute', 'fixed'):
        for side in ('left', 'top', 'right', 'bottom'):
            if (p := to_px(style.get(side))) is not None and p <= -999:
                reasons.append(f"position:{pos}; {side}:{style[side]}")
                break
    if (ti := to_px(style.get('text-indent'))) is not None and ti <= -999:
        reasons.append(f"text-indent:{style['text-indent']}")
    for k in ('width', 'height'):
        if (p := to_px(style.get(k))) is not None and p == 0 and \
                style.get('overflow', '').strip() == 'hidden':
            reasons.append(f"{k}:0; overflow:hidden")
            break
    if (c := style.get('clip-path', '').strip()) and 'inset(100%' in c.replace(' ', ''):
        reasons.append("clip-path 로 가림")
    if (c := style.get('clip', '').strip()) and re.search(r'rect\(\s*0[a-z]*\s*,?\s*0', c):
        reasons.append("clip 으로 가림")
    return " / ".join(reasons) or None
