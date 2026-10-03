"""크몽 포트폴리오용 샘플 리포트.

승인된 날 포트폴리오가 비어 있으면 첫 거래가 안 나온다. 실제 고객 사례가
생기기 전까지 이것이 바닥을 깐다.

**예시 데이터라는 것을 숨기지 않는다.** 도구 화면에 이미 '(예시 데이터)' 가
찍혀 나오고, 표지와 각 쪽에도 적는다. 진짜 거래인 척하면 그게 조작이다.
보여줄 것은 '내가 이런 걸 만들어 드린다' 이지 '내가 이만큼 팔았다' 가 아니다.

만드는 법
  python3 scripts/shoot_sample.py     먼저 화면을 찍고
  python3 scripts/make_portfolio.py   그 다음 이것

  OUT_DIR  결과를 쓸 폴더. 없으면 package/portfolio
"""
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
SHOT = Path(os.environ.get("SHOT_DIR", "/tmp/pf"))
OUT = Path(os.environ.get("OUT_DIR", ROOT / "package" / "portfolio"))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

CSS = """
@page { size: A4; margin: 15mm 15mm 12mm; }
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Noto Sans CJK KR',sans-serif;font-size:10.5pt;line-height:1.62;
  color:#111;word-break:keep-all}
h1{font-size:19pt;font-weight:700;letter-spacing:-.03em;line-height:1.3;margin-bottom:2mm}
.lead{font-size:11pt;color:#444;margin-bottom:4mm;line-height:1.6}
.tag{display:inline-block;font-size:9pt;font-weight:700;color:#8A6D00;
  background:#FDF3D7;border:.6pt solid #E0C97A;padding:.8mm 2.4mm;border-radius:1mm;
  margin-bottom:3mm}
h2{font-size:12.5pt;font-weight:700;margin:6mm 0 1.6mm;padding-bottom:1.2mm;
  border-bottom:1pt solid #222;break-after:avoid}
h3{font-size:10.8pt;font-weight:700;margin:3.6mm 0 1.2mm;break-after:avoid}
p{margin-bottom:1.8mm;text-align:justify}
b{font-weight:700}
ul{margin:1.2mm 0 2.2mm 5.5mm}
li{margin-bottom:1mm}
figure{margin:2.2mm 0 3mm}
figure img{width:100%;border:.5pt solid #C8C8C8}
figcaption{font-size:8.8pt;color:#666;margin-top:1.2mm;text-align:center}
table{width:100%;border-collapse:collapse;margin:2mm 0 2.6mm;font-size:9.6pt}
th,td{border:.5pt solid #9A9A9A;padding:1.4mm 2mm;text-align:left;line-height:1.45;
  vertical-align:top}
th{background:#EFEFEC;font-weight:700}
tr{break-inside:avoid}
.note{font-size:9.2pt;color:#555;line-height:1.55;margin:1.5mm 0 2.5mm}
.foot{margin-top:5mm;padding-top:2.5mm;border-top:.5pt solid #BBB;
  font-size:9pt;color:#555;line-height:1.55}
.pb{break-before:page}
"""


def body():
    return f"""
<span class="tag">예시 데이터로 만든 샘플입니다 · 실제 거래 내역이 아닙니다</span>
<h1>정산 엑셀을 보내주시면<br>이런 리포트를 만들어 드립니다</h1>
<p class="lead">아래는 <b>예시용으로 만든 가짜 정산 파일</b>로 실제 작업 과정을 그대로 돌린
결과입니다. 의뢰하시면 받으시게 될 결과물이 이렇게 생겼습니다.</p>

<h2>1. 얼마가 남았는지</h2>
<figure><img src="file://{SHOT}/01_손익결과.png">
<figcaption>순이익과 마진율, 그리고 그 숫자가 어디서 깎였는지</figcaption></figure>
<p>정산서는 <b>통장에 얼마가 들어오는지까지만</b> 알려줍니다. 거기서 원가와 광고비를
빼야 실제로 남은 돈이 나오는데, 그 두 가지가 정산 파일에 아예 없습니다.
그래서 매출 611만원이 순이익 192만원이 되는 과정이 보이지 않습니다.</p>
<p>이 표는 그 과정을 펼칩니다. 수수료가 매출의 6.9%, 원가가 54.3%, 광고비가 7.4%.
어디가 무거운지 한 줄로 보입니다.</p>

<h2>2. 어떤 상품이 벌고 어떤 상품이 까먹는지</h2>
<figure><img src="file://{SHOT}/02_상품별순이익.png">
<figcaption>많이 남은 순으로 정렬. 왼쪽으로 뻗은 막대가 적자 상품</figcaption></figure>
<p><b>여기가 핵심입니다.</b> 전체 마진율 31.5%만 보면 괜찮아 보입니다. 그런데 쪼개 보면
<b>팔수록 손해인 상품이 2개</b> 섞여 있습니다. 잘 팔리는 상품이 번 돈에 묻혀서
총액만 봐서는 안 보입니다.</p>

<h2 class="pb">3. 그 적자 상품, 얼마면 본전인지</h2>
<figure><img src="file://{SHOT}/03_본전판매가.png">
<figcaption>순이익이 0이 되는 판매가. 수수료가 같이 오르는 것까지 넣어 계산</figcaption></figure>
<p>적자라는 것만 알려드리면 반쪽입니다. <b>얼마로 올려야 본전인지</b>까지 냅니다.</p>
<p>계산에 한 가지를 더 넣었습니다. 판매가를 올리면 <b>수수료도 같이 오릅니다.</b>
수수료가 판매가에 비례하기 때문입니다. 그것을 빼고 계산하면 올려도 여전히 적자인
금액이 나옵니다. 그래서 수수료율을 변수로 두고 풀었습니다.</p>
<div class="note">예시의 유기농 아몬드 1kg은 22,900원에 팔아 개당 적자였고,
<b>24,381원</b>이 되어야 순이익이 0이 됩니다. 단순히 원가를 더해 나눈 값과는 다릅니다.</div>

<h2>4. 숫자가 어디서 나왔는지</h2>
<figure><img src="file://{SHOT}/04_상세내역.png">
<figcaption>상품별 전체 내역. 엑셀로 붙여 넣을 수 있게 같이 드립니다</figcaption></figure>
<p>처음 보는 사람이 만든 숫자입니다. <b>믿으시라고 하지 않고 확인하실 수 있게</b>
드립니다. 이상해 보이는 곳을 말씀해 주시면 원본 파일의 어느 행에서 나온 값인지
짚어 드립니다.</p>

<h2 class="pb">보내주실 것은 두 가지입니다</h2>
<table>
<tr><th style="width:26%">무엇을</th><th>어디서</th></tr>
<tr><td><b>정산 내역 엑셀</b></td>
    <td>스마트스토어는 판매관리 안의 정산관리에서, 쿠팡은 판매자센터 정산 메뉴에서
    받으실 수 있습니다. 한 달치면 충분하고, 받은 파일을 손대지 말고 그대로 주세요</td></tr>
<tr><td><b>상품별 매입 원가</b></td>
    <td>상품명과 개당 원가만 적어 주시면 됩니다. 엑셀이든 메모든 상관없습니다.
    이것이 없으면 순이익이 나오지 않습니다</td></tr>
</table>
<p class="note">광고비와 택배비는 아시면 주시고, 모르시면 빼고 계산합니다.
여러 마켓을 하시면 각각 보내주시면 한 장으로 합쳐 드립니다.</p>

<h3>보내시기 전에 지워 주실 것</h3>
<p><b>구매자 이름, 연락처, 주소가 들어 있으면 그 열을 통째로 지우고 보내주세요.</b>
계산에 쓰지 않는 정보이고, 제가 받지 않는 편이 서로 안전합니다.
주문번호·상품명·금액·수수료만 있으면 됩니다.</p>

<h2>이런 분께 쓸모가 있습니다</h2>
<ul>
<li>정산서를 봐도 <b>어떤 상품이 돈을 벌고 있는지</b> 모르겠는 분</li>
<li>전체 마진율은 괜찮은데 <b>통장에 남는 게 없는</b> 것 같은 분</li>
<li>원가가 올랐는데 <b>판매가를 얼마로 올려야 할지</b> 모르겠는 분</li>
<li>엑셀 수식을 만지는 데 매달 <b>몇 시간씩 쓰고 계신</b> 분</li>
</ul>

<h2>미리 말씀드리는 것</h2>
<table>
<tr><th style="width:34%">상황</th><th>어떻게 됩니다</th></tr>
<tr><td>마켓이 파일 형식을 바꾼 경우</td>
    <td>컬럼을 자동으로 못 잡을 수 있습니다. 그때는 직접 맞추면 되고, 추가 비용은 없습니다</td></tr>
<tr><td>광고비를 상품별로 모르시는 경우</td>
    <td>전체 금액으로만 반영됩니다. 상품별 적자 판정은 그만큼 보수적으로 봐야 합니다</td></tr>
<tr><td>반품·교환이 많이 얽힌 달</td>
    <td>숫자가 흔들릴 수 있습니다. 그런 달은 미리 말씀드립니다</td></tr>
</table>

<div class="foot">이 문서의 모든 숫자는 <b>예시용으로 만든 가짜 정산 파일</b>에서 나온 것입니다.
실제 거래 내역이나 고객 자료가 아닙니다. 결과물의 모양을 보여드리기 위한 샘플입니다.</div>
"""


def main():
    missing = [n for n in ("01_손익결과", "02_상품별순이익", "03_본전판매가", "04_상세내역")
               if not (SHOT / f"{n}.png").exists()]
    if missing:
        raise SystemExit(f"화면 사진이 없다: {missing}\n먼저 scripts/shoot_sample.py 를 돌린다.")

    OUT.mkdir(parents=True, exist_ok=True)
    html = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            f'<title>샘플 리포트</title><style>{CSS}</style></head>'
            f'<body>{body()}</body></html>')
    tmp = OUT / "_샘플리포트.html"
    tmp.write_text(html, encoding="utf-8")
    pdf = OUT / "샘플리포트(예시데이터).pdf"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={pdf}",
                    f"file://{tmp}"], check=True, capture_output=True)
    tmp.unlink()

    # 크몽 포트폴리오는 이미지로 올린다. 쪽마다 PNG 로도 뽑아 둔다.
    import pymupdf
    d = pymupdf.open(pdf)
    for i, page in enumerate(d, 1):
        page.get_pixmap(dpi=150).save(OUT / f"포트폴리오_{i}쪽.png")
    print(f"{pdf.name}  {pdf.stat().st_size // 1024}KB  {d.page_count}쪽")
    print(f"쪽별 PNG {d.page_count}장도 같이 만들었다 → {OUT}")


if __name__ == "__main__":
    main()
