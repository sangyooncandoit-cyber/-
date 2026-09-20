"""테스트용 가짜 정산 파일 생성기.

실제 정산 파일을 구할 수 없으므로, 공개된 수수료 구조와
현실적인 '지저분함'(상단 제목행, 콤마 숫자, 반품 음수행, 합계행)을
재현한 샘플을 만든다. 도구 파서를 검증하는 것이 목적이다.

정답(ground truth)을 같이 내보내서 계산 검증에 쓴다.
"""
import json
import random
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
SAMPLE = BASE / "sample"
FEES = json.loads((BASE / "src" / "fees.json").read_text(encoding="utf-8"))

random.seed(20260920)

PRODUCTS = [
    # (상품명, 판매가, 매입원가, 카테고리)
    ("무선 블루투스 이어폰 화이트", 39900, 21000, "디지털/가전"),
    ("스테인리스 텀블러 500ml", 15900, 6800, "생활용품"),
    ("유기농 아몬드 1kg", 22900, 21000, "식품"),        # 수입 원가 급등 — 적자 전환
    ("면 100% 기본 티셔츠 블랙", 19900, 7200, "의류/패션"),
    ("실리콘 주방 집게 2p", 8900, 8200, "생활용품"),     # 최저가 경쟁 — 사실상 마진 없음
    ("비타민D 1000IU 90정", 18900, 9100, "건강기능식품"),
    ("USB-C 고속 충전 케이블 2m", 12900, 3300, "디지털/가전"),
    ("캠핑용 폴딩 의자", 45900, 28000, "기타"),
    ("핸드드립 커피 원두 200g", 16900, 9800, "식품"),
    ("극세사 클리닝 타월 5p", 9900, 3100, "생활용품"),
]


def won(n):
    """콤마 찍힌 문자열 — 실제 엑셀에서 흔히 텍스트로 저장되는 형태."""
    return f"{int(round(n)):,}"


def build_rows():
    """주문 단위 원시 데이터와 정답을 함께 만든다."""
    rows = []
    order_no = 20260901000
    for day in range(1, 31):
        for name, price, cost, cat in PRODUCTS:
            # 상품마다 판매 빈도를 다르게
            n_orders = random.choices([0, 1, 2, 3], weights=[45, 30, 17, 8])[0]
            for _ in range(n_orders):
                order_no += 1
                qty = random.choices([1, 2, 3], weights=[75, 20, 5])[0]
                is_return = random.random() < 0.06  # 반품률 6%
                rows.append({
                    "날짜": f"2026-09-{day:02d}",
                    "주문번호": str(order_no),
                    "상품명": name,
                    "카테고리": cat,
                    "수량": qty,
                    "판매단가": price,
                    "매입원가": cost,
                    "반품": is_return,
                })
    return rows


def smartstore_file(rows):
    """스마트스토어형: 상단 제목행 2줄 + 콤마 숫자 + 합계행."""
    pay_rate = FEES["smartstore"]["payment_fee"]["일반"] / 100     # 3.63% VAT 포함
    sales_rate = FEES["smartstore"]["sales_fee"]["네이버쇼핑_연동"] / 100  # 2.73% VAT 별도
    vat = FEES["vat_rate"] / 100

    out, truth = [], []
    for r in rows:
        sign = -1 if r["반품"] else 1
        gross = r["판매단가"] * r["수량"] * sign
        pay_fee = round(gross * pay_rate)
        sales_fee = round(gross * sales_rate * (1 + vat))  # VAT 별도 → 부가세 붙여 차감
        coupon = round(gross * 0.01) if random.random() < 0.25 else 0
        settle = gross - pay_fee - sales_fee - coupon
        cogs = r["매입원가"] * r["수량"] * sign

        out.append({
            "정산완료일": r["날짜"],
            "주문번호": r["주문번호"],
            "상품명": r["상품명"],
            "구분": "반품" if r["반품"] else "판매",
            "수량": sign * r["수량"],
            "결제금액": won(gross),
            "결제수수료": won(pay_fee),
            "판매수수료": won(sales_fee),
            "쿠폰분담금": won(coupon),
            "정산금액": won(settle),
        })
        truth.append({
            "상품명": r["상품명"], "수량": sign * r["수량"], "매출": gross,
            "수수료합": pay_fee + sales_fee + coupon, "정산금액": settle, "원가": cogs,
        })

    df = pd.DataFrame(out)
    # 합계행 — 실제 파일에 자주 붙어 있고 파서를 망가뜨리는 원인
    total = {c: "" for c in df.columns}
    total["정산완료일"] = "합계"
    total["정산금액"] = won(sum(t["정산금액"] for t in truth))
    df = pd.concat([df, pd.DataFrame([total])], ignore_index=True)

    path = SAMPLE / "샘플_스마트스토어_정산내역_202609.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        # 상단에 제목/기간 2줄을 띄워 헤더를 3행부터 시작시킨다
        df.to_excel(w, index=False, sheet_name="정산내역", startrow=2)
        ws = w.sheets["정산내역"]
        ws["A1"] = "스마트스토어 정산내역 (샘플 · 실제 데이터 아님)"
        ws["A2"] = "조회기간: 2026-09-01 ~ 2026-09-30"
    return path, truth


def coupang_file(rows):
    """쿠팡형: 헤더 1행, 카테고리별 수수료, 광고비는 별도 시트."""
    cat_fees = FEES["coupang"]["category_fee"]
    out, truth = [], []
    for r in rows:
        sign = -1 if r["반품"] else 1
        gross = r["판매단가"] * r["수량"] * sign
        rate = cat_fees.get(r["카테고리"], cat_fees["기타"]) / 100
        fee = round(gross * rate)
        settle = gross - fee
        cogs = r["매입원가"] * r["수량"] * sign
        out.append({
            "정산일": r["날짜"],
            "주문번호": r["주문번호"],
            "등록상품명": r["상품명"],
            "판매수량": sign * r["수량"],
            "판매금액": gross,
            "판매수수료": -fee,
            "정산대상금액": settle,
        })
        truth.append({
            "상품명": r["상품명"], "수량": sign * r["수량"], "매출": gross,
            "수수료합": fee, "정산금액": settle, "원가": cogs,
        })

    df = pd.DataFrame(out)
    # 광고비: 상품별 월 집계 (매출 상위 상품에 더 집행했다고 가정)
    ad = {}
    for t in truth:
        ad.setdefault(t["상품명"], 0)
        ad[t["상품명"]] += max(0, t["매출"]) * 0.04
    ad_df = pd.DataFrame(
        [{"상품명": k, "광고비": round(v)} for k, v in sorted(ad.items())]
    )

    path = SAMPLE / "샘플_쿠팡_정산내역_202609.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as w:
        df.to_excel(w, index=False, sheet_name="정산내역")
        ad_df.to_excel(w, index=False, sheet_name="광고비")
    return path, truth, ad_df


def cost_file():
    """셀러가 따로 관리하는 원가표 (도구에 함께 넣는 입력)."""
    df = pd.DataFrame(
        [{"상품명": n, "매입원가": c} for n, _, c, _ in PRODUCTS]
    )
    path = SAMPLE / "샘플_상품원가표.xlsx"
    df.to_excel(path, index=False, sheet_name="원가")
    return path


def main():
    SAMPLE.mkdir(parents=True, exist_ok=True)
    rows = build_rows()

    ss_path, ss_truth = smartstore_file(rows)
    cp_path, cp_truth, ad_df = coupang_file(rows)
    cost_path = cost_file()

    # 정답 저장 — 도구 계산 결과와 대조할 기준
    pd.DataFrame(ss_truth).to_csv(SAMPLE / "_truth_smartstore.csv", index=False)
    pd.DataFrame(cp_truth).to_csv(SAMPLE / "_truth_coupang.csv", index=False)
    ad_df.to_csv(SAMPLE / "_truth_coupang_ad.csv", index=False)

    print(f"주문 행 수: {len(rows)}")
    for p in (ss_path, cp_path, cost_path):
        print(f"  생성: {p.name}  ({p.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
