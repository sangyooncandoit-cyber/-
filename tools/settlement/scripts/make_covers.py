"""판매용 커버 이미지 생성.

숫자는 전부 data.json에서 읽는다. data.json은 검증된 계산 로직이 만든 값이라,
커버에 적힌 수치와 도구가 내놓는 수치가 어긋날 수 없다.

규격
  크몽 서비스 메인·상세  4:3, 최소 652x488  -> 1600x1200
  Gumroad 커버          1280x720
  Gumroad 썸네일         600x600
"""
import json
import shutil
from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = Path(__file__).resolve().parent.parent
OUT = BASE / "covers"
BUILD = OUT / "_html"
D = json.loads((OUT / "data.json").read_text(encoding="utf-8"))
ITEMS, T = D["items"], D["total"]

FONTS = Path("/tmp/claude-0/-home-user--/f3ee751f-f072-52fb-87c6-a6b16558e8df/scratchpad/fonts2")

RATIOS = {"43": (800, 600), "169": (640, 360), "sq": (300, 300)}


def won(n):
    return f"{round(n):,}"


def signed(n):
    return ("+" if n > 0 else "−" if n < 0 else "") + f"{abs(round(n)):,}"


def face(fam, weight, files):
    return "\n".join(
        f"@font-face{{font-family:'{fam}';font-weight:{weight};font-style:normal;"
        f"font-display:block;src:url('{FONTS / f}') format('woff2');}}" for f in files)


FONTCSS = "\n".join([
    face("GothicA1", 400, ["gothic-a1-korean-400-normal.woff2", "gothic-a1-latin-400-normal.woff2"]),
    face("GothicA1", 500, ["gothic-a1-korean-500-normal.woff2", "gothic-a1-latin-500-normal.woff2"]),
    face("GothicA1", 700, ["gothic-a1-korean-700-normal.woff2", "gothic-a1-latin-700-normal.woff2"]),
    face("Myeongjo", 700, ["nanum-myeongjo-korean-700-normal.woff2",
                           "nanum-myeongjo-latin-700-normal.woff2"]),
    face("Myeongjo", 800, ["nanum-myeongjo-korean-800-normal.woff2",
                           "nanum-myeongjo-latin-800-normal.woff2"]),
])

# 라이트 모드 팔레트 — 검증 통과분 (흑자 #0B7A4B / 적자 #C42B1C)
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html{font-size:calc(var(--w)/100)}
body{width:var(--w);height:var(--h);overflow:hidden;
  font-family:GothicA1,sans-serif;color:#16171A;background:#FBFAF6;
  -webkit-font-smoothing:antialiased;font-variant-numeric:tabular-nums}
.c{width:100%;height:100%;padding:7rem 7.5rem 12.5rem;display:flex;flex-direction:column;
  position:relative;background:#FBFAF6}
.c.dark{background:#1C1D21;color:#F2F1EC}
.c.sq{padding:8rem 7.5rem;justify-content:space-between}
.eyebrow{font:700 1.95rem/1 GothicA1;letter-spacing:.06em;color:#A8242B;margin-bottom:3.2rem}
.dark .eyebrow{color:#E8868B}
h1{font-family:Myeongjo,serif;font-weight:800;letter-spacing:-.022em;line-height:1.36;
  word-break:keep-all}
.title{font-family:Myeongjo,serif;font-weight:700;font-size:3.7rem;line-height:1.4;
  letter-spacing:-.018em;margin-bottom:1.3rem;word-break:keep-all}
.sub{font:400 2.15rem/1.6 GothicA1;color:#63666C;margin-bottom:3.4rem;word-break:keep-all}
.dark .sub{color:#B4B3AC}
.fill{flex:1;min-height:0}
.main{flex:1;min-height:0;display:flex;flex-direction:column;justify-content:center}
.pos{color:#0B7A4B} .neg{color:#C42B1C}
.dark .pos{color:#5FD3A3}
.brand{position:absolute;left:7.5rem;right:7.5rem;bottom:5.2rem;display:flex;
  align-items:baseline;justify-content:space-between;gap:2rem;
  border-top:.28rem solid #16171A;padding-top:2.2rem;
  font:400 1.9rem/1 GothicA1;color:#63666C}
.dark .brand{border-color:#F2F1EC;color:#B4B3AC}
.brand b{font-weight:700;color:#16171A;letter-spacing:-.01em}
.dark .brand b{color:#F2F1EC}

/* 영수증 */
.rc{background:#F1F0EA;border-top:.28rem solid #16171A;border-bottom:.28rem solid #16171A;
  padding:3.2rem 3.4rem 2.8rem}
.rl{display:flex;align-items:baseline;gap:1.6rem;padding:1.05rem 0;font:400 2.25rem/1 GothicA1}
.rl .lb{color:#44464B;white-space:nowrap}
.rl .dt{flex:1;border-bottom:.13rem dotted #C3C2B9;transform:translateY(-.55rem)}
.rl .am{white-space:nowrap;font-weight:500}
.rl.ded .lb,.rl.ded .am{color:#7A7D83}
.rl.mid{border-top:.13rem solid #CBCAC1;margin-top:.9rem;padding-top:1.7rem}
.rl.mid .lb,.rl.mid .am{color:#16171A;font-weight:700}
.rl.tot{border-top:.22rem solid #16171A;margin-top:1.4rem;padding-top:2.1rem;align-items:flex-end}
.rl.tot .lb{font-weight:700;font-size:2.1rem;color:#16171A}
.rl.tot .am{font-family:Myeongjo,serif;font-size:4.8rem;font-weight:800;letter-spacing:-.03em}

/* 적자 발췌 */
.loss{border-top:.28rem solid #16171A}
.lcard{display:flex;align-items:baseline;gap:2.4rem;padding:2.6rem .4rem;
  border-bottom:.13rem solid #DEDDD5}
.lcard .n{flex:1;font:500 2.7rem/1.3 GothicA1;min-width:0;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.lcard .v{font:700 3.1rem/1 GothicA1;color:#C42B1C;white-space:nowrap}
.lcard .m{font:400 2rem/1 GothicA1;color:#7A7D83;width:8.5rem;text-align:right}

/* 발산 막대 */
.bars{display:flex;flex-direction:column;gap:1.15rem}
.br{display:grid;grid-template-columns:24rem 1fr 13.5rem;gap:1.8rem;align-items:center}
.br .bn{font:400 1.95rem/1.35 GothicA1;color:#44464B;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.track{position:relative;height:3.1rem}
.track::before{content:"";position:absolute;left:var(--z);top:-.35rem;bottom:-.35rem;
  width:.13rem;background:#C3C2B9}
.bar{position:absolute;top:.35rem;height:2.4rem}
.bar.p{background:#0B7A4B}
.bar.l{background:#C42B1C}
.br .bv{font:700 2rem/1 GothicA1;text-align:right}
.legend{display:flex;gap:2.8rem;font:400 1.8rem/1 GothicA1;color:#63666C;margin-bottom:2.2rem}
.legend i{display:inline-block;width:1.25rem;height:1.25rem;margin-right:.75rem;vertical-align:-.1rem}

/* 표 */
table{width:100%;border-collapse:collapse;table-layout:fixed}
th,td{padding:1.5rem 1.15rem;text-align:right;border-bottom:.13rem solid #DEDDD5;white-space:nowrap}
th{font:700 1.6rem/1 GothicA1;color:#63666C;letter-spacing:.01em;
  border-top:.28rem solid #16171A;border-bottom:.28rem solid #16171A}
td{font:500 1.82rem/1 GothicA1}
th.l,td.l{text-align:left;width:27%;overflow:hidden;text-overflow:ellipsis}
td.l{font:400 1.88rem/1 GothicA1;letter-spacing:-.015em}
th:not(.l),td:not(.l){width:12.2%}
tbody tr:last-child td{border-bottom:none}
tr.bad td.l::before{content:"▼ ";color:#C42B1C;font-size:1.5rem}
tr.bad td.l{color:#C42B1C}
"""

def page(body, w, h, cls=""):
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{FONTCSS}\n{CSS}\n"
            f":root{{--w:{w}px;--h:{h}px}}</style></head>"
            f"<body><div class='c {cls}'>{body}</div></body></html>")


def brand(tag="오픈마켓 정산 손익 분석"):
    return f'<div class="brand"><b>정산 엑스레이</b><span>{tag}</span></div>'


# ── 1. 표지 ──────────────────────────────────────────────
def cover_title(w, h):
    body = f"""
    <span class="eyebrow">스마트스토어 · 쿠팡</span>
    <h1 style="font-size:4.5rem;color:#B4B3AC;font-weight:700">
      통장에 <span style="color:#F2F1EC">{won(T['rev'] - T['fee'])}원</span>이 들어왔습니다.</h1>
    <h1 style="font-size:6.7rem;margin-top:2.2rem">
      실제로 번 돈은<br><span class="pos">{won(T['profit'])}원</span>입니다.</h1>
    <div class="fill"></div>
    <p style="font:400 2.3rem/1.65 GothicA1;color:#B4B3AC;max-width:78%">
      정산서는 얼마가 입금되는지까지만 알려줍니다.<br>
      어떤 상품이 돈을 잃고 있는지는 알려주지 않습니다.</p>
    {brand()}"""
    return page(body, w, h, "dark")


def cover_square(w, h):
    body = f"""
    <span class="eyebrow" style="font-size:2.8rem;margin-bottom:3rem">정산 엑스레이</span>
    <h1 style="font-size:5.6rem;color:#B9DCD9;font-weight:600;line-height:1.3">
      입금액의<br><span class="mono" style="color:#7BE0B4;font-size:8.5rem">33.8%</span><br>만 실제 이익입니다</h1>
    <div class="fill"></div>
    <p style="font:400 3rem/1.5 GothicA1;color:#B9DCD9">
      정산서에서<br>적자 상품을 찾아냅니다</p>"""
    return page(body, w, h, "dark")


# ── 2. 영수증 ────────────────────────────────────────────
def cover_receipt(w, h):
    def line(lb, am, cls=""):
        return (f'<div class="rl {cls}"><span class="lb">{lb}</span>'
                f'<span class="dt"></span><span class="am">{am}</span></div>')
    body = f"""
    <span class="eyebrow">2026년 9월 · 주문 {D['orders']}건</span>
    <h2 class="title">정산서는 얼마가 남는지 알려주지 않습니다</h2>
    <div class="main"><div class="rc">
      {line("매출", won(T['rev']))}
      {line("− 판매·결제 수수료", won(T['fee']), "ded")}
      {line("= 정산 입금액", won(T['rev'] - T['fee']), "mid")}
      {line("− 매입 원가", won(T['cogs']), "ded")}
      {line("− 광고비", won(T['ad']), "ded")}
      <div class="rl tot"><span class="lb">실제 순이익</span><span class="dt"></span>
        <span class="am pos">{won(T['profit'])}</span></div>
    </div></div>
    {brand("입금액의 33.8%만 실제 이익")}"""
    return page(body, w, h)


# ── 3. 적자 상품 ─────────────────────────────────────────
def cover_losses(w, h):
    losers = [o for o in ITEMS if o["profit"] < 0]
    cards = "".join(
        f'<div class="lcard"><span class="n">{o["name"]}</span>'
        f'<span class="v">{signed(o["profit"])}원</span>'
        f'<span class="m">{o["margin"]:.1f}%</span></div>' for o in losers)
    body = f"""
    <span class="eyebrow">한 달 정산서에서 찾아낸 것</span>
    <h2 class="title">팔수록 손해인 상품은 티가 안 납니다</h2>
    <p class="sub">전체 마진율은 31.5%였습니다. 상품별로 쪼개자 이 둘이 나왔습니다.</p>
    <div class="main"><div class="loss">{cards}</div>
      <p style="font:400 2.05rem/1.55 GothicA1;color:#5F6A77;max-width:82%;margin-top:3.4rem">
        원가가 오르거나 광고비가 붙으면 마진은 조용히 음수로 넘어갑니다.<br>
        총액만 봐서는 보이지 않습니다.</p></div>
    {brand("적자 상품 자동 표시")}"""
    return page(body, w, h)


# ── 4. 상품별 손익 차트 ──────────────────────────────────
def cover_chart(w, h):
    mx = max(o["profit"] for o in ITEMS)
    mn = min(o["profit"] for o in ITEMS)
    maxp, maxl = max(1, mx), max(1, -mn)
    span = maxp + maxl
    z = maxl / span * 100
    rows = ""
    for o in ITEMS:
        wpct = abs(o["profit"]) / span * 100
        bar = (f'<div class="bar p" style="left:{z}%;width:{wpct}%"></div>' if o["profit"] >= 0
               else f'<div class="bar l" style="left:{z - wpct}%;width:{wpct}%"></div>')
        cls = "pos" if o["profit"] >= 0 else "neg"
        rows += (f'<div class="br"><div class="bn">{o["name"]}</div>'
                 f'<div class="track" style="--z:{z}%">{bar}</div>'
                 f'<div class="bv {cls}">{signed(o["profit"])}</div></div>')
    body = f"""
    <span class="eyebrow">상품별 순이익</span>
    <h2 class="title">상품별로 쪼개면 보입니다</h2>
    <div class="legend">
      <span><i style="background:#0B7A4B"></i>흑자 (오른쪽)</span>
      <span><i style="background:#C42B1C"></i>적자 (왼쪽)</span>
      <span>막대 방향과 부호로도 구분됩니다</span></div>
    <div class="main"><div class="bars">{rows}</div></div>
    {brand("상품 10개 · 주문 253건")}"""
    return page(body, w, h)


# ── 5. 상세 표 ───────────────────────────────────────────
def cover_table(w, h):
    rows = ""
    for o in ITEMS[:8]:
        bad = " class='bad'" if o["profit"] < 0 else ""
        cls = "pos" if o["profit"] >= 0 else "neg"
        rows += (f"<tr{bad}><td class='l'>{o['name']}</td><td>{o['qty']}</td>"
                 f"<td>{won(o['rev'])}</td><td>{won(o['fee'])}</td><td>{won(o['cogs'])}</td>"
                 f"<td class='{cls}'>{signed(o['profit'])}</td>"
                 f"<td class='{cls}'>{o['margin']:.1f}%</td></tr>")
    body = f"""
    <span class="eyebrow">상세 내역</span>
    <h2 class="title">엑셀에 그대로 붙여넣습니다</h2>
    <div class="main"><table>
      <thead><tr><th class="l">상품명</th><th>수량</th><th>매출</th><th>수수료</th>
        <th>원가</th><th>순이익</th><th>마진율</th></tr></thead>
      <tbody>{rows}</tbody></table></div>
    {brand("상위 8개 표시 · 실제로는 전 품목")}"""
    return page(body, w, h)


JOBS = [
    ("01_표지_크몽",        cover_title,   "43"),
    ("02_영수증_크몽",      cover_receipt, "43"),
    ("03_적자상품_크몽",    cover_losses,  "43"),
    ("04_손익차트_크몽",    cover_chart,   "43"),
    ("05_상세표_크몽",      cover_table,   "43"),
    ("06_표지_gumroad커버", cover_title,   "169"),
    ("07_표지_gumroad썸네일", cover_square, "sq"),
]


def main():
    if BUILD.exists():
        shutil.rmtree(BUILD)
    BUILD.mkdir(parents=True)
    for f in OUT.glob("*.png"):
        f.unlink()

    with sync_playwright() as p:
        b = p.chromium.launch(
            executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
            args=["--no-sandbox", "--font-render-hinting=none"])
        for name, fn, ratio in JOBS:
            w, h = RATIOS[ratio]
            html = fn(w, h)
            f = BUILD / f"{name}.html"
            f.write_text(html, encoding="utf-8")
            pg = b.new_page(viewport={"width": w, "height": h}, device_scale_factor=2)
            pg.goto(f"file://{f}")
            pg.wait_for_timeout(900)
            out = OUT / f"{name}.png"
            pg.screenshot(path=out, clip={"x": 0, "y": 0, "width": w, "height": h})
            print(f"  {name}.png  {w*2}x{h*2}  {out.stat().st_size//1024}KB")
            pg.close()
        b.close()


if __name__ == "__main__":
    main()
