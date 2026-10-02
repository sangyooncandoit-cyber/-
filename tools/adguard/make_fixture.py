"""정답을 아는 테스트 사이트를 만든다.

주최 측 평가 사이트는 공개되지 않는다. 그래서 공고문 붙임1 의 기법 설명과
붙임4 의 작성 예시를 근거로 같은 모양의 사이트를 직접 만들고, 어디에 무엇을
심었는지 정답표를 함께 적어둔다.

이게 있어야 '몇 개를 놓쳤는지'와 '몇 개를 잘못 신고했는지'를 숫자로 볼 수 있다.
정산 도구를 만들 때 썼던 방법과 같다.
"""
import json
from pathlib import Path

from winout import force_utf8

OUT = Path(__file__).parent / "fixture"
ANSWERS = []


def add(page, location, technique, evidence):
    ANSWERS.append({"page": page, "location": location,
                    "technique": technique, "evidence_text": evidence})


CSS = """
body { font-family: sans-serif; background:#ffffff; color:#222; margin:2em }
.notice-board { border:1px solid #ddd; padding:1em }
.visually-hidden { position:absolute; left:-9999px }
.ghost { color: #ffffff }
.tiny { font-size: 0px }
.gone { display: none }
.faded { opacity: 0 }
.sr-only { position:absolute; left:-9999px }   /* 정상 용도 — 오탐 함정 */
nav.menu .sub { display:none }                  /* 정상 용도 — 오탐 함정 */
"""

PAGES = {}

# ── 목록 페이지 ────────────────────────────────────────────────
PAGES["index.html"] = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>○○시청 공지사항</title><link rel="stylesheet" href="style.css"></head><body>
<nav class="menu"><a href="index.html">홈</a>
  <span class="sub">숨겨진 하위 메뉴입니다</span></nav>
<h1>공지사항</h1>
<div class="notice-board">
  <span class="sr-only">본문 바로가기</span>
  <table><tbody>
    <tr><td class="title"><a href="view.html?id=1024">제1024호 민원 안내</a></td></tr>
    <tr><td class="title"><a href="view.html?id=1180">제1180호 재난 문자 안내</a></td></tr>
    <tr><td class="title"><a href="view.html?id=1181">ｍｅｇａ－ＢＥＴ 첫충 30％ 지급</a></td></tr>
  </tbody></table>
</div>
<iframe src="widget.html" width="300" height="80"></iframe>
</body></html>"""
add("index.html", "div.notice-board > table > tbody > tr:nth-of-type(3) > td.title > a",
    "HOMOGLYPH", "ｍｅｇａ－ＢＥＴ 첫충 30％ 지급")

# ── 게시글 1 ───────────────────────────────────────────────────
PAGES["view.html?id=1024"] = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>제1024호</title><link rel="stylesheet" href="style.css"></head><body>
<h1>제1024호 민원 안내</h1>
<div class="article-body">
  <p>민원 접수는 평일 9시부터 18시까지입니다.</p>
  <p class="desc"><span class="ghost">ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ 코드 LUCKY7</span></p>
</div>
<div class="comments">
  <p class="c">감사합니다.</p>
  <p class="c"><span style="font-size:0px">먹튀검증 안전놀이터 상담 텔레그램 @promo_777</span></p>
</div>
</body></html>"""
add("view.html?id=1024", "div.article-body > p.desc > span.ghost", "JAMO",
    "ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ 코드 LUCKY7")
add("view.html?id=1024", "div.article-body > p.desc > span.ghost", "TRANSPARENT",
    "ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ 코드 LUCKY7")
add("view.html?id=1024", "div.comments > p.c:nth-of-type(2) > span", "OFFSCREEN",
    "먹튀검증 안전놀이터 상담 텔레그램 @promo_777")

# ── 게시글 2 ───────────────────────────────────────────────────
PAGES["view.html?id=1180"] = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>제1180호</title><link rel="stylesheet" href="style.css"></head><body>
<h1>제1180호 재난 문자 안내</h1>
<div class="article-body">
  <p>재난 문자는 기상청 기준에 따라 발송됩니다.</p>
  <div class="gone">무료 슬롯 체험 바로가기 jackpot-win.vip</div>
  <p class="faded">바카라 환전 보증업체 안내</p>
  <p class="normal">자세한 내용은 담당 부서로 문의하세요.</p>
</div>
</body></html>"""
add("view.html?id=1180", "div.article-body > div.gone", "OFFSCREEN",
    "무료 슬롯 체험 바로가기 jackpot-win.vip")
add("view.html?id=1180", "div.article-body > p.faded", "TRANSPARENT",
    "바카라 환전 보증업체 안내")

# ── iframe 안쪽 ────────────────────────────────────────────────
PAGES["widget.html"] = """<!doctype html><html lang="ko"><head><meta charset="utf-8">
<link rel="stylesheet" href="style.css"></head><body>
<div class="wrap"><span class="tiny">홀덤 포커 가입코드 ABC123</span>
<span>오늘의 날씨</span></div>
</body></html>"""
add("widget.html|iframe", 'iframe[src="widget.html"] >>> div.wrap > span.tiny',
    "OFFSCREEN", "홀덤 포커 가입코드 ABC123")


def main():
    force_utf8()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "style.css").write_text(CSS, encoding="utf-8")
    for name, html in PAGES.items():
        # ?id=1024 같은 이름을 파일로 쓰려고 바꿔 둔다 (로컬 서버가 매핑)
        (OUT / name.replace("?", "__")).write_text(html, encoding="utf-8")
    (OUT / "answers.json").write_text(
        json.dumps(ANSWERS, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"페이지 {len(PAGES)}개, 정답 {len(ANSWERS)}건")
    for a in ANSWERS:
        print(f"  {a['technique']:12s} {a['page']:22s} {a['evidence_text'][:34]}")


if __name__ == "__main__":
    main()
