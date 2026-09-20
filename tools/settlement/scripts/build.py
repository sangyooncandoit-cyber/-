"""템플릿 + core.js + 샘플 데이터 → 단일 HTML.

정식판과 라이트판을 같은 소스에서 만든다. 라이트는 LITE 플래그 하나로
갈리므로 두 판의 계산 결과가 어긋날 수 없다.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
tpl = (BASE / "src" / "index.template.html").read_text(encoding="utf-8")
core = (BASE / "src" / "core.js").read_text(encoding="utf-8")
sample = (BASE / "src" / "sample_embed.json").read_text(encoding="utf-8")

BUILDS = [
    ("index.html", "false", "정산 엑스레이"),
    ("lite.html",  "true",  "정산 엑스레이 Lite"),
]

dist = BASE / "dist"
dist.mkdir(exist_ok=True)

for filename, lite, title in BUILDS:
    out = (tpl
           .replace("/*__CORE__*/", core)
           .replace("/*__SAMPLE__*/", sample)
           .replace("/*__LITE__*/", lite)
           .replace("<title>정산 엑스레이</title>", f"<title>{title}</title>"))
    for token in ("/*__CORE__*/", "/*__SAMPLE__*/", "/*__LITE__*/"):
        assert token not in out, f"{filename}: {token} 치환 실패"
    assert f"<title>{title}</title>" in out, f"{filename}: 제목 치환 실패"
    (dist / filename).write_text(out, encoding="utf-8")
    print(f"  {filename}  ({len(out.encode()):,} bytes)  LITE={lite}")
