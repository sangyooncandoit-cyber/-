"""GitHub Pages 배포본 생성.

아티팩트로 발행할 때는 뼈대가 씌워지지만, 직접 호스팅하면 그렇지 않다.
charset이 없으면 한글이 깨지므로 완전한 문서로 감싼다.
카톡이나 카페에 링크를 붙였을 때 미리보기가 뜨도록 OG 태그도 넣는다.
"""
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
DEPLOY = BASE / "deploy"
SITE = "https://sangyooncandoit-cyber.github.io/settlement-xray"

PAGES = [
    dict(src=BASE / "dist" / "lite.html", out="index.html",
         title="정산 엑스레이 — 오픈마켓 정산 손익 분석",
         desc="정산 엑셀을 넣으면 상품별 실제 순이익과 적자 상품이 나옵니다. "
              "설치도 가입도 없고, 정산 파일이 기기 밖으로 나가지 않습니다.",
         url=SITE + "/",
         swap=[(SITE + "/pro/", "pro/")]),
    dict(src=BASE / "landing" / "index.html", out="pro/index.html",
         title="통장에 찍힌 돈, 다 내 돈일까 — 정산 엑스레이",
         desc="정산 입금액의 33.8%만 실제 이익이었습니다. "
              "상품별로 쪼개면 팔수록 손해인 상품이 보입니다.",
         url=SITE + "/pro/",
         swap=[("https://claude.ai/artifact/BA2SCuYfrjucy7veU2qMHh", "../")]),
]

SKEL = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="{desc}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="정산 엑스레이">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}/cover.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<style>:root{{color-scheme:light}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
{body}
</head>
<body>
</body>
</html>
"""


def main():
    DEPLOY.mkdir(exist_ok=True)
    for p in PAGES:
        html = p["src"].read_text(encoding="utf-8")
        for old, new in p["swap"]:
            assert old in html, f"{p['out']}: 바꿀 문자열을 찾지 못함"
            html = html.replace(old, new)
        assert "claude.ai" not in html, f"{p['out']}: claude.ai 링크가 남았다"

        out = SKEL.format(title=p["title"], desc=p["desc"], url=p["url"],
                          site=SITE, body=html)
        dst = DEPLOY / p["out"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(out, encoding="utf-8")
        print(f"  {p['out']}  ({len(out.encode()):,} bytes)")

    (DEPLOY / ".nojekyll").write_text("", encoding="utf-8")
    # 링크 미리보기용 이미지
    import shutil
    shutil.copy(BASE / "covers" / "06_표지_gumroad커버.png", DEPLOY / "cover.png")
    print(f"  cover.png  ({(DEPLOY/'cover.png').stat().st_size:,} bytes)")
    print(f"  .nojekyll")


if __name__ == "__main__":
    main()
