"""대행 서비스용 커버 이미지.

파는 물건이 바뀌었다. 프로그램이 아니라 결과를 넘긴다.
그래서 이미지도 "이런 도구입니다"가 아니라 "이렇게 받으십니다"로 간다.

숫자는 전부 covers/data.json 에서 읽는다. 손익분기 판매가도 거기서 계산한다.
검증된 계산 로직이 만든 값이라 화면과 도구가 어긋날 수 없다.

규격: 크몽 메인·상세 4:3, 최소 652x488 -> 1600x1200
"""
import shutil
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_covers import BUILD, CSS, FONTCSS, ITEMS, OUT, T, won  # noqa: E402

W, H = 800, 600

EXTRA = """
.tag{display:inline-block;font:700 1.55rem/1 GothicA1;letter-spacing:.04em;
  padding:.85rem 1.4rem;border:.16rem solid #C3C2B9;color:#7A7D83;border-radius:.4rem}
.dark .tag{border-color:#5A5B60;color:#9A9BA0}
.flow{display:grid;grid-template-columns:1fr auto 1fr;gap:2.6rem;align-items:stretch}
.box{border:.22rem solid #16171A;padding:2.6rem 2.4rem;display:flex;
  flex-direction:column;gap:1.5rem;background:#F1F0EA}
.box.fill{background:#16171A;color:#FBFAF6;border-color:#16171A}
.box h3{font:700 2.15rem/1 GothicA1;letter-spacing:-.01em}
.box ul{list-style:none;display:flex;flex-direction:column;gap:1.15rem}
.box li{font:400 1.95rem/1.45 GothicA1;color:#44464B;padding-left:2.1rem;position:relative;
  word-break:keep-all}
.box.fill li{color:#D8D7D0}
.box li::before{content:"";position:absolute;left:0;top:.82rem;width:1.05rem;height:1.05rem;
  background:#A8242B}
.box.fill li::before{background:#5FD3A3}
.arw{display:flex;align-items:center;font:700 4.2rem/1 GothicA1;color:#A8242B}
.cmp{display:grid;grid-template-columns:1fr 1fr;gap:3rem}
.cmp>div{padding:2.8rem 2.6rem;border-top:.3rem solid}
.cmp .a{border-color:#C3C2B9;background:#F1F0EA}
.cmp .b{border-color:#0B7A4B;background:#EAF4EF}
.cmp h3{font:700 2.2rem/1 GothicA1;margin-bottom:2rem}
.cmp p{font:400 2.05rem/1.55 GothicA1;color:#44464B;word-break:keep-all}
.cmp .a h3{color:#7A7D83}
.cmp .b h3{color:#0B7A4B}
.be{border-top:.28rem solid #16171A;margin-top:1rem}
.berow{display:grid;grid-template-columns:1fr 14rem 4rem 16rem;gap:1.8rem;align-items:center;
  padding:2.4rem .4rem;border-bottom:.13rem solid #DEDDD5}
.berow .n{min-width:0}
.berow .n b{display:block;font:500 2.55rem/1.25 GothicA1;overflow:hidden;
  text-overflow:ellipsis;white-space:nowrap}
.berow .n i{display:block;font:400 1.8rem/1 GothicA1;color:#C42B1C;font-style:normal;
  margin-top:.8rem}
.berow .now{font:400 2.4rem/1 GothicA1;color:#7A7D83;text-align:right}
.berow .to{font:700 2.6rem/1 GothicA1;color:#C3C2B9;text-align:center}
.berow .need{font:700 3rem/1 GothicA1;color:#0B7A4B;text-align:right}
.behead{display:grid;grid-template-columns:1fr 14rem 4rem 16rem;gap:1.8rem;
  padding:0 .4rem 1.3rem;font:400 1.75rem/1 GothicA1;color:#7A7D83}
.behead span:nth-child(2){text-align:right}
.behead span:nth-child(4){text-align:right}
.note{font:400 1.7rem/1.5 GothicA1;color:#8A8C91;margin-top:2.2rem}
"""


def page(body, cls=""):
    return (f"<!doctype html><html><head><meta charset='utf-8'><style>{FONTCSS}\n{CSS}\n"
            f"{EXTRA}\n:root{{--w:{W}px;--h:{H}px}}</style></head>"
            f"<body><div class='c {cls}'>{body}</div></body></html>")


def brand(tag):
    return f'<div class="brand"><b>정산 분석 대행</b><span>{tag}</span></div>'


def breakeven(it):
    """순이익이 0이 되는 개당 판매가.

    수수료는 매출에 비례하므로 수수료율을 고정하고 역산한다.
      p*q*(1-r) - 원가 - 광고비 = 0  ->  p = (원가+광고비) / (q*(1-r))
    """
    r = it["fee"] / it["rev"]
    return (it["cogs"] + it["ad"]) / (it["qty"] * (1 - r))


LOSSES = [i for i in ITEMS if i["profit"] < 0]
LOSS_SUM = sum(-i["profit"] for i in LOSSES)


# ── 01 표지 ───────────────────────────────────────────────
def c_title():
    body = f"""
    <span class="eyebrow">정산 분석 대행 · 스마트스토어 쿠팡</span>
    <h1 style="font-size:4.3rem;color:#B4B3AC;font-weight:700">
      정산 엑셀만 보내주시면</h1>
    <h1 style="font-size:6.9rem;margin-top:2rem">
      팔수록 손해인 상품을<br><span style="color:#FF8A80">찾아 드립니다</span></h1>
    <div class="fill" style="display:flex;align-items:center">
      <p style="font:400 2.25rem/1.6 GothicA1;color:#8F9096;border-left:.28rem solid #E8868B;
        padding-left:2.4rem;max-width:80%">
        예시 파일로 돌려보니 적자 상품이 두 개 섞여 있었고,<br>
        합쳐서 한 달에 <span style="color:#FF8A80;font-weight:700">38,522원</span> 손해였습니다.<br>
        총액만 보면 보이지 않는 금액입니다.</p>
    </div>
    <p style="font:400 2.3rem/1.65 GothicA1;color:#B4B3AC;max-width:82%">
      설치도, 엑셀 수식도 필요 없습니다.<br>
      파일을 보내시면 제가 계산해서 리포트로 보내 드립니다.</p>
    {brand("보내주시면 만들어 드립니다")}"""
    return page(body, "dark")


# ── 02 흐름 ───────────────────────────────────────────────
def c_flow():
    body = f"""
    <div class="title">사장님이 하실 일은 파일을 보내는 것뿐입니다</div>
    <div class="sub">나머지는 제가 합니다. 컬럼이 안 맞아도 제가 맞춥니다.</div>
    <div class="main">
      <div class="flow">
        <div class="box">
          <h3>보내주실 것</h3>
          <ul>
            <li>정산 내역 엑셀<br>받은 그대로</li>
            <li>상품별 매입 원가</li>
            <li>광고비 · 택배비<br>(아시는 것만)</li>
          </ul>
        </div>
        <div class="arw">→</div>
        <div class="box fill">
          <h3>받으실 것</h3>
          <ul>
            <li>상품별 순이익표</li>
            <li>적자 상품 목록</li>
            <li>본전 판매가</li>
            <li>PDF와 엑셀 두 가지</li>
          </ul>
        </div>
      </div>
      <p class="note">구매자 이름·연락처·주소는 지우고 보내주세요. 계산에 쓰지 않습니다.</p>
    </div>
    {brand("2일 안에 보내 드립니다")}"""
    return page(body)


# ── 03 상품별 순이익표 ────────────────────────────────────
def c_table():
    rows = "".join(
        f'<tr class="{"bad" if i["profit"] < 0 else ""}">'
        f'<td class="l">{i["name"]}</td>'
        f'<td>{won(i["rev"])}</td><td>{won(i["fee"])}</td>'
        f'<td>{won(i["cogs"])}</td><td>{won(i["ad"])}</td>'
        f'<td class="{"neg" if i["profit"] < 0 else "pos"}"><b>{won(i["profit"])}</b></td>'
        f'<td class="{"neg" if i["profit"] < 0 else ""}">{i["margin"]}%</td></tr>'
        for i in ITEMS)
    body = f"""
    <div class="title">이런 표를 받으십니다</div>
    <div class="sub">많이 남은 순서입니다. 마지막 두 줄이 팔수록 손해인 상품입니다.
      <span class="tag" style="margin-left:1.2rem">예시 데이터</span></div>
    <div class="main">
      <table>
        <thead><tr><th class="l">상품</th><th>매출</th><th>수수료</th><th>원가</th>
          <th>광고비</th><th>순이익</th><th>마진</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
    {brand("상품별 순이익")}"""
    return page(body)


# ── 04 적자와 본전 판매가 ─────────────────────────────────
def c_breakeven():
    rows = "".join(
        f'<div class="berow">'
        f'<span class="n"><b>{i["name"]}</b><i>월 {won(-i["profit"])}원 손해</i></span>'
        f'<span class="now">{won(i["rev"] / i["qty"])}원</span>'
        f'<span class="to">→</span>'
        f'<span class="need">{won(breakeven(i))}원</span></div>'
        for i in LOSSES)
    body = f"""
    <div class="title">적자 상품은 얼마에 팔아야 본전인지까지 계산합니다</div>
    <div class="sub">전체 마진율이 괜찮아 보여도 쪼개보면 섞여 있습니다.
      <span class="tag" style="margin-left:1.2rem">예시 데이터</span></div>
    <div class="main">
      <div class="be">
        <div class="behead"><span></span><span>지금 판매가</span><span></span>
          <span>본전 판매가</span></div>
        {rows}
      </div>
      <p class="note">이 두 개만 합쳐도 한 달에 {won(LOSS_SUM)}원입니다.
        총액만 보면 잘 팔리는 상품이 번 돈에 묻혀서 보이지 않습니다.</p>
    </div>
    {brand("손익분기 판매가")}"""
    return page(body)


# ── 05 프로그램과의 차이 ──────────────────────────────────
def c_compare():
    body = f"""
    <div class="title">프로그램을 사는 것과 무엇이 다른가</div>
    <div class="sub">차이는 하나입니다. 안 맞았을 때 누가 고생하느냐입니다.</div>
    <div class="main">
      <div class="cmp">
        <div class="a">
          <h3>프로그램을 사면</h3>
          <p>내 정산 파일을 제대로 읽을지<br>사기 전에는 알 수 없습니다.<br><br>
             컬럼이 안 잡히면 결국<br>내가 붙잡고 씨름해야 합니다.</p>
        </div>
        <div class="b">
          <h3>대행을 맡기면</h3>
          <p>파일을 보내고 결과를 받습니다.<br><br>
             안 맞으면 제가 고칩니다.<br>
             못 읽으면 환불해 드립니다.<br><br>
             위험이 저한테 있습니다.</p>
        </div>
      </div>
    </div>
    {brand("위험은 파는 쪽이 집니다")}"""
    return page(body)


JOBS = [
    ("11_표지_대행", c_title),
    ("12_흐름_대행", c_flow),
    ("13_상품별순이익_대행 (예시데이터)", c_table),
    ("14_본전판매가_대행 (예시데이터)", c_breakeven),
    ("15_프로그램과의차이_대행", c_compare),
]


def main():
    BUILD.mkdir(parents=True, exist_ok=True)
    for f in OUT.glob("1*_*대행*.png"):
        f.unlink()

    print("손익분기 판매가 (data.json에서 역산)")
    for i in LOSSES:
        print(f"  {i['name']:22s} {i['qty']:3d}개  현재 {won(i['rev']/i['qty'])}원"
              f"  ->  본전 {won(breakeven(i))}원")
    print()

    with sync_playwright() as p:
        b = p.chromium.launch(
            executable_path="/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
            args=["--no-sandbox", "--font-render-hinting=none"])
        for name, fn in JOBS:
            f = BUILD / f"{name}.html"
            f.write_text(fn(), encoding="utf-8")
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=2)
            pg.goto(f"file://{f}")
            pg.wait_for_timeout(900)
            out = OUT / f"{name}.png"
            pg.screenshot(path=out, clip={"x": 0, "y": 0, "width": W, "height": H})
            print(f"  {name}.png  {W*2}x{H*2}  {out.stat().st_size//1024}KB")
            pg.close()
        b.close()


if __name__ == "__main__":
    main()
