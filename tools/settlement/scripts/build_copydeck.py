"""크몽·Gumroad 문구 마크다운 → 블록별 복사 버튼이 달린 단일 HTML."""
import html
import json
import re
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
COPY = BASE / "copy"


def parse(md: str):
    """마크다운을 블록 목록으로. 코드펜스는 복사 대상, 나머지는 설명."""
    blocks, lines, i = [], md.split("\n"), 0
    while i < len(lines):
        ln = lines[i]
        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i]); i += 1
            i += 1
            blocks.append(("code", "\n".join(buf)))
        elif ln.startswith("###"):
            blocks.append(("h3", ln.lstrip("# ").strip())); i += 1
        elif ln.startswith("##"):
            blocks.append(("h2", ln.lstrip("# ").strip())); i += 1
        elif ln.startswith("# "):
            i += 1  # 문서 제목은 탭 이름으로 대체
        elif ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip("> ").rstrip()); i += 1
            blocks.append(("note", " ".join(x for x in buf if x)))
        elif ln.strip():
            buf = []
            while i < len(lines) and lines[i].strip() and not lines[i].startswith(("#", "```", ">")):
                buf.append(lines[i].rstrip()); i += 1
            blocks.append(("p", " ".join(buf)))
        else:
            i += 1
    return blocks


def inline(t: str) -> str:
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`(.+?)`", r"<code>\1</code>", t)
    return t


def render(blocks):
    out, n = [], 0
    for kind, text in blocks:
        if kind == "code":
            n += 1
            out.append(
                f'<div class="blk"><button class="cp" type="button" data-i="{n}">복사</button>'
                f'<pre id="b{n}">{html.escape(text)}</pre></div>')
        elif kind == "h2":
            out.append(f"<h2>{inline(text)}</h2>")
        elif kind == "h3":
            out.append(f"<h3>{inline(text)}</h3>")
        elif kind == "note":
            out.append(f'<p class="note">{inline(text)}</p>')
        else:
            out.append(f"<p>{inline(text)}</p>")
    return "\n".join(out)


TABS = [("kmong", "크몽"), ("gumroad", "Gumroad")]
panes = []
for key, label in TABS:
    body = render(parse((COPY / f"{key}.md").read_text(encoding="utf-8")))
    panes.append(f'<div class="pane" id="p-{key}"{"" if key == "kmong" else " hidden"}>{body}</div>')

tabs = "".join(
    f'<button class="tab{" on" if k == "kmong" else ""}" data-t="{k}" type="button">{l}</button>'
    for k, l in TABS)

page = f"""<title>판매 문구 덱</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
:root{{
  --ground:#F2F5F7;--paper:#FFF;--sunk:#E7ECF0;
  --ink:#131920;--ink-2:#3A4451;--muted:#606A77;--line:#DBE1E7;--line-2:#C3CBD4;
  --accent:#0E5158;--accent-soft:#DFEDEE;--warn:#8A5A00;--warn-soft:#FBF2E1;
  --sans:"IBM Plex Sans KR",-apple-system,"Malgun Gothic","Apple SD Gothic Neo",sans-serif;
  --mono:"IBM Plex Mono",Consolas,monospace;
}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{
  --ground:#0C1116;--paper:#151B22;--sunk:#111820;
  --ink:#E6EBF1;--ink-2:#BCC5D0;--muted:#8A94A1;--line:#232B35;--line-2:#333D49;
  --accent:#57B5AB;--accent-soft:#102528;--warn:#D9A441;--warn-soft:#2A2113;}}}}
:root[data-theme="dark"]{{
  --ground:#0C1116;--paper:#151B22;--sunk:#111820;
  --ink:#E6EBF1;--ink-2:#BCC5D0;--muted:#8A94A1;--line:#232B35;--line-2:#333D49;
  --accent:#57B5AB;--accent-soft:#102528;--warn:#D9A441;--warn-soft:#2A2113;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);
  font-size:15px;line-height:1.7;-webkit-font-smoothing:antialiased}}
.wrap{{max-width:780px;margin:0 auto;padding-inline:16px;padding-block:0 60px}}
.bar{{position:sticky;top:env(safe-area-inset-top,0px);z-index:9;background:var(--ground);
  border-bottom:1px solid var(--line);margin-inline:-16px;padding:11px 16px 0}}
.bar h1{{font-size:16px;font-weight:700;margin:0 0 10px;letter-spacing:-.01em}}
.tabs{{display:flex;gap:4px}}
.tab{{font:500 14px var(--sans);padding:8px 16px;border:1px solid var(--line);border-bottom:none;
  background:var(--sunk);color:var(--muted);border-radius:7px 7px 0 0;cursor:pointer}}
.tab.on{{background:var(--paper);color:var(--accent);font-weight:600;
  box-shadow:inset 0 2px 0 var(--accent)}}
.tab:focus-visible{{outline:2px solid var(--accent);outline-offset:-2px}}
h2{{font-size:18px;font-weight:600;margin:32px 0 10px;letter-spacing:-.02em;
  padding-bottom:7px;border-bottom:1px solid var(--line)}}
h3{{font-size:15px;font-weight:600;margin:22px 0 8px;color:var(--accent)}}
p{{margin:0 0 12px;color:var(--ink-2);max-width:64ch}}
p.note{{background:var(--warn-soft);border:1px solid var(--line);border-left:3px solid var(--warn);
  border-radius:6px;padding:12px 14px;font-size:13.5px;color:var(--ink-2)}}
code{{font-family:var(--mono);font-size:12.5px;background:var(--sunk);padding:1px 5px;border-radius:4px}}
.blk{{position:relative;margin:0 0 14px}}
pre{{font-family:var(--mono);font-size:12.5px;line-height:1.65;background:var(--paper);
  border:1px solid var(--line);border-radius:7px;padding:40px 15px 15px;margin:0;
  white-space:pre-wrap;word-break:break-word;color:var(--ink);overflow-x:auto}}
.cp{{position:absolute;top:8px;right:8px;font:500 12px var(--sans);padding:5px 12px;
  border:1px solid var(--line-2);border-radius:6px;background:var(--sunk);color:var(--ink-2);
  cursor:pointer;z-index:1}}
.cp:hover{{border-color:var(--accent);color:var(--accent)}}
.cp:focus-visible{{outline:2px solid var(--accent);outline-offset:2px}}
.cp.done{{background:var(--accent);border-color:var(--accent);color:#fff}}
@media (prefers-reduced-motion:reduce){{*{{transition:none!important}}}}
</style>
<div class="wrap">
  <div class="bar"><h1>판매 문구 덱</h1><div class="tabs">{tabs}</div></div>
  {"".join(panes)}
</div>
<script>
document.querySelectorAll(".tab").forEach(t => t.onclick = () => {{
  document.querySelectorAll(".tab").forEach(x => x.classList.toggle("on", x === t));
  document.querySelectorAll(".pane").forEach(p => p.hidden = p.id !== "p-" + t.dataset.t);
  window.scrollTo({{top: 0}});
}});
document.querySelectorAll(".cp").forEach(b => b.onclick = async () => {{
  const text = document.getElementById("b" + b.dataset.i).textContent;
  try {{ await navigator.clipboard.writeText(text); }}
  catch {{
    const r = document.createRange();
    r.selectNodeContents(document.getElementById("b" + b.dataset.i));
    const s = getSelection(); s.removeAllRanges(); s.addRange(r);
    b.textContent = "선택됨"; setTimeout(() => b.textContent = "복사", 2000); return;
  }}
  b.textContent = "복사함"; b.classList.add("done");
  setTimeout(() => {{ b.textContent = "복사"; b.classList.remove("done"); }}, 1800);
}});
</script>
"""

dist = BASE / "dist"
dist.mkdir(exist_ok=True)
(dist / "copydeck.html").write_text(page, encoding="utf-8")
blocks = page.count('class="cp"')
print(f"빌드 완료: dist/copydeck.html ({len(page.encode()):,} bytes, 복사 블록 {blocks}개)")
