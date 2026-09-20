"""크몽·Gumroad에 올릴 판매 패키지(zip) 생성.

크몽은 HTML 단독 업로드를 지원 형식으로 안내하지 않는다
(PPT/PDF/HWP/DOCS 등 문서 형식). 여러 파일은 ZIP으로 등록할 수 있으므로
도구·안내문·예시 파일을 묶어 하나의 ZIP으로 만든다.
"""
import shutil
import zipfile
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DELIV = BASE / "deliverable"
SAMPLE = BASE / "sample"
OUT = BASE / "package"

GUIDE = """정산 엑스레이 — 사용 안내
====================================

구매해 주셔서 감사합니다.


■ 여는 법

  "정산엑스레이.html" 파일을 더블클릭하세요.
  브라우저에서 바로 열립니다. 설치할 것은 없습니다.

  처음 열면 예시 데이터가 들어 있어, 어떻게 동작하는지
  먼저 보실 수 있습니다.


■ 처음 쓰실 때 (30분이면 끝납니다)

  1. 마켓에서 지난달 정산 파일을 내려받습니다
       스마트스토어 : 정산관리 > 정산내역 > 다운로드
       쿠팡         : 정산 > 매출내역 > 엑셀 받기

  2. 도구에 끌어다 놓습니다
       함께 들어있는 "예시_정산내역.xlsx" 로 먼저 연습하셔도 됩니다

  3. 컬럼이 맞게 잡혔는지 봅니다
       상품명·수량·매출·수수료 네 가지만 맞으면 됩니다
       틀리면 화면에서 직접 바꿀 수 있습니다

  4. 상품별 매입원가를 넣습니다
       여기가 제일 오래 걸립니다. 하지만 한 번만 하면 됩니다.
       품목이 많으면 매출 상위 20개만 먼저 넣어도 큰 그림이 나옵니다
       한 번 넣으면 브라우저에 저장돼 다음에 열 때 그대로 있습니다

  5. 그 달 광고비 총액을 넣습니다

  6. 적자 상품부터 봅니다
       빨간색으로 먼저 올라옵니다


■ 계산식

  순이익 = 매출 − 수수료 − 원가 − 광고비

  반품은 음수 행으로 인식해 매출·수수료·원가에서 함께 뺍니다.
  수수료 부호는 마켓마다 +/− 표기가 다른데, 매출 부호와 비교해
  자동으로 맞춥니다.


■ 파일은 어디로도 전송되지 않습니다

  이 도구에는 서버가 없습니다. 계산은 전부 브라우저 안에서
  끝납니다. 인터넷을 끊고 쓰셔도 똑같이 동작합니다.
  (글꼴만 인터넷에서 받아오므로, 오프라인에서는 글꼴이
   기기 기본값으로 바뀝니다. 계산에는 영향이 없습니다.)


■ 이건 못 합니다

  · 세무 신고용이 아닙니다.
    부가세·배송비·재고 평가는 계산에 넣지 않습니다.
  · 매입원가는 직접 넣으셔야 합니다.
    정산 파일에 없는 정보라 자동으로 알 수 없습니다.
  · 광고비는 상품별 매출 비중으로 배분합니다.
  · 여러 마켓 합산은 아직 안 됩니다. 파일 하나씩 분석합니다.


■ 잘 안 될 때

  컬럼이 자동으로 안 잡히거나 숫자가 이상하면 알려주세요.
  정산 양식은 마켓마다 달라서, 알려주시면 맞춰 드립니다.

  받아보시고 내 정산 파일에 안 맞으면 7일 안에 말씀만 주세요.
  이유를 묻지 않고 전액 환불해 드립니다.


■ 포함된 파일

  정산엑스레이.html   도구 본체
  사용안내.txt        이 문서
  예시_정산내역.xlsx  연습용 예시 파일 (실제 데이터 아님)


엑셀 파서로 SheetJS 0.18.5 (Apache-2.0)를 포함합니다.
"""

# (zip 이름, 배포판 파일, zip 안에 들어갈 이름)
PACKAGES = [
    ("정산엑스레이_v1.zip",      "정산엑스레이.html",      "정산엑스레이.html"),
    ("정산엑스레이_Lite_v1.zip", "정산엑스레이_Lite.html", "정산엑스레이_Lite.html"),
]


def main():
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True)

    guide = OUT / "사용안내.txt"
    # 윈도우 메모장에서 깨지지 않도록 BOM 포함 UTF-8로 쓴다
    guide.write_text(GUIDE, encoding="utf-8-sig")

    for zipname, toolname, innername in PACKAGES:
        src = DELIV / toolname
        assert src.exists(), f"{toolname} 없음 — build.py 먼저 실행"
        path = OUT / zipname
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
            z.write(src, innername)
            z.write(guide, "사용안내.txt")
            z.write(SAMPLE / "샘플_스마트스토어_정산내역_202609.xlsx", "예시_정산내역.xlsx")
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            bad = z.testzip()
        assert bad is None, f"{zipname} 손상: {bad}"
        print(f"  {zipname}  {path.stat().st_size//1024}KB  → {', '.join(names)}")

    guide.unlink()


if __name__ == "__main__":
    main()
