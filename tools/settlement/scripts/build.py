"""템플릿 + core.js + 샘플 데이터 → 단일 HTML.

정식판과 라이트판을 같은 소스에서 만든다. 라이트는 LITE 플래그 하나로
갈리므로 두 판의 계산 결과가 어긋날 수 없다.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
tpl = (BASE / "src" / "index.template.html").read_text(encoding="utf-8")
core = (BASE / "src" / "core.js").read_text(encoding="utf-8")
sample = (BASE / "src" / "sample_embed.json").read_text(encoding="utf-8")

# 공개 사이트 주소. 여기 한 곳만 바꾸면 모든 판에 반영된다.
SITE = "https://sangyooncandoit-cyber.github.io/settlement-xray"

BUILDS = [
    ("index.html", "false", "정산 엑스레이"),
    ("lite.html",  "true",  "정산 엑스레이 Lite"),
]

# 판매용 배포판: 구매자가 파일을 내려받아 디스크에서 바로 연다.
# 아티팩트와 달리 스켈레톤이 씌워지지 않으므로 완전한 HTML로 감싸고,
# 엑셀 파서를 인라인해서 인터넷 없이도 파일 분석이 되게 한다.
DIST_BUILDS = [
    ("정산엑스레이.html",      "false", "정산 엑스레이"),
    ("정산엑스레이_Lite.html", "true",  "정산 엑스레이 Lite"),
]
CDN_TAG = ('<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/'
           '0.18.5/xlsx.full.min.js"></script>')


def standalone(body: str) -> str:
    """디스크에서 여는 파일용 껍데기. 아티팩트 스켈레톤과 같은 전제를 만든다."""
    return ('<!doctype html>\n<html lang="ko">\n<head>\n'
            '<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width,initial-scale=1,'
            'viewport-fit=cover">\n'
            '<style>:root{color-scheme:light}body{margin:0}'
            'img{max-width:100%}[hidden]{display:none!important}</style>\n'
            + body + '\n</head>\n<body>\n</body>\n</html>\n')

dist = BASE / "dist"
dist.mkdir(exist_ok=True)

def render(lite: str, title: str, buy_url: str = SITE + "/pro/") -> str:
    out = (tpl
           .replace("/*__CORE__*/", core)
           .replace("/*__SAMPLE__*/", sample)
           .replace("/*__LITE__*/", lite)
           .replace("/*__BUY_URL__*/", buy_url)
           .replace("<title>정산 엑스레이</title>", f"<title>{title}</title>"))
    for token in ("/*__CORE__*/", "/*__SAMPLE__*/", "/*__LITE__*/", "/*__BUY_URL__*/"):
        assert token not in out, f"{token} 치환 실패"
    assert f"<title>{title}</title>" in out, "제목 치환 실패"
    assert "claude.ai" not in out, "claude.ai 참조가 남았다"
    return out


for filename, lite, title in BUILDS:
    out = render(lite, title)
    (dist / filename).write_text(out, encoding="utf-8")
    print(f"  {filename}  ({len(out.encode()):,} bytes)  LITE={lite}")

# ── 판매용 배포판 ────────────────────────────────────────
xlsx = (BASE / "vendor" / "xlsx.full.min.js").read_text(encoding="utf-8")
assert "</script" not in xlsx, "인라인 불가: 라이브러리에 닫는 스크립트 태그가 있다"
deliver = BASE / "deliverable"
deliver.mkdir(exist_ok=True)

for filename, lite, title in DIST_BUILDS:
    out = render(lite, title)
    assert CDN_TAG in out, "CDN 스크립트 태그를 찾지 못했다"
    # 인터넷 없이도 엑셀을 읽을 수 있도록 파서를 파일 안에 넣는다
    out = out.replace(CDN_TAG, "<script>/*! SheetJS 0.18.5 (Apache-2.0) */\n" + xlsx + "</script>")
    out = standalone(out)
    assert "cdnjs.cloudflare.com" not in out, "CDN 참조가 남았다"
    assert out.startswith("<!doctype html>"), "독립 실행용 껍데기가 빠졌다"
    (deliver / filename).write_text(out, encoding="utf-8")
    print(f"  deliverable/{filename}  ({len(out.encode()):,} bytes)  LITE={lite}")
