"""템플릿 + core.js + 샘플 데이터 → 단일 HTML 파일."""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
tpl = (BASE / "src" / "index.template.html").read_text(encoding="utf-8")
core = (BASE / "src" / "core.js").read_text(encoding="utf-8")
sample = (BASE / "src" / "sample_embed.json").read_text(encoding="utf-8")

out = tpl.replace("/*__CORE__*/", core).replace("/*__SAMPLE__*/", sample)

for token in ("/*__CORE__*/", "/*__SAMPLE__*/"):
    assert token not in out, f"{token} 치환 실패"

dist = BASE / "dist"
dist.mkdir(exist_ok=True)
path = dist / "index.html"
path.write_text(out, encoding="utf-8")
print(f"빌드 완료: {path.relative_to(BASE.parent.parent)}  ({len(out.encode()):,} bytes)")
