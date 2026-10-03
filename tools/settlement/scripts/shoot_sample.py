"""포트폴리오에 넣을 결과 화면을 찍는다.

도구를 샘플 데이터로 돌려 결과 영역만 잘라 낸다. 손으로 캡처하지 않는 이유는
도구를 고칠 때마다 다시 찍어야 하기 때문이다.

  python3 scripts/shoot_sample.py      → /tmp/pf 에 네 장
"""
import os
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(os.environ.get("SHOT_DIR", "/tmp/pf"))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
SCALE = 2

# 결과 화면의 제목 → 잘라 낼 구간. 제목 위치는 매번 다시 읽는다.
CUTS = [("손익 결과", "01_손익결과"), ("상품별 순이익", "02_상품별순이익"),
        ("얼마면 본전인가", "03_본전판매가"), ("상세 내역", "04_상세내역")]


def main():
    from playwright.sync_api import sync_playwright
    from PIL import Image

    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=CHROME)
        pg = b.new_page(viewport={"width": 1000, "height": 1400},
                        device_scale_factor=SCALE)
        pg.goto("file://" + str(ROOT / "deliverable" / "정산엑스레이.html"))
        time.sleep(1)
        pg.get_by_text("샘플로 둘러보기").first.click()
        time.sleep(3)
        heads = pg.eval_on_selector_all(
            "h1,h2,h3",
            "e=>e.map(x=>({t:x.innerText.trim(), "
            "y:x.getBoundingClientRect().top+scrollY}))")
        pg.screenshot(path=str(OUT / "full.png"), full_page=True)
        b.close()

    ys = [h["y"] for h in heads]
    im = Image.open(OUT / "full.png")
    for key, name in CUTS:
        idx = next((i for i, h in enumerate(heads) if key in h["t"]), None)
        if idx is None:
            print(f"  건너뜀 — 화면에서 '{key}' 를 못 찾았다")
            continue
        top = ys[idx]
        bottom = ys[idx + 1] if idx + 1 < len(ys) else top + 460
        im.crop((0, int(top * SCALE), im.width,
                 min(int(bottom * SCALE), im.height))).save(OUT / f"{name}.png")
        print(f"  {name}.png")
    print(f"→ {OUT}")


if __name__ == "__main__":
    main()
