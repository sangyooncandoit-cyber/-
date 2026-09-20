"""검증용 fixture 생성 — 현재 샘플 파일과 정답을 묶는다."""
import json
from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parent.parent
S = BASE / "sample"

def grid(path, sheet=0):
    df = pd.read_excel(path, sheet_name=sheet, header=None)
    return [[("" if pd.isna(v) else (v if isinstance(v, (int, float)) else str(v))) for v in r]
            for _, r in df.iterrows()]

grids = {
    "smartstore": grid(S / "샘플_스마트스토어_정산내역_202609.xlsx"),
    "coupang": grid(S / "샘플_쿠팡_정산내역_202609.xlsx", "정산내역"),
}
costs = {r["상품명"]: int(r["매입원가"]) for _, r in pd.read_excel(S / "샘플_상품원가표.xlsx").iterrows()}

truth = {}
for key, f in (("smartstore", "_truth_smartstore.csv"), ("coupang", "_truth_coupang.csv")):
    g = (pd.read_csv(S / f).groupby("상품명")
         .agg(qty=("수량", "sum"), rev=("매출", "sum"), fee=("수수료합", "sum"), cogs=("원가", "sum"))
         .reset_index())
    g["profit"] = g["rev"] - g["fee"] - g["cogs"]
    truth[key] = {r["상품명"]: {k: float(r[k]) for k in ("qty", "rev", "fee", "cogs", "profit")}
                  for _, r in g.iterrows()}

(S / "_fixtures.json").write_text(
    json.dumps({"grids": grids, "truth": truth, "costs": costs}, ensure_ascii=False), encoding="utf-8")
print("fixtures 갱신:", {k: len(v) for k, v in grids.items()})
