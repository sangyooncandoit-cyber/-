"""윈도우 빌드 경로 확인용 최소 프로그램.

진짜 탐지 도구를 만들기 전에, 리눅스에서 쓴 파이썬이 윈도우에서 빌드되고
실행까지 되는지부터 확인한다. 여기서 막히면 이 공모전은 시작할 수 없다.

확인하는 것
  - PyInstaller 단일 exe 빌드가 되는가
  - 그 exe 가 윈도우에서 실제로 실행되는가
  - 한글 출력과 UTF-8 파일 쓰기가 깨지지 않는가
  - 실제 탐지에 쓸 라이브러리들이 번들에 들어가는가
  - exe 용량이 메일로 보낼 만한가
"""
import json
import platform
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

KST = timezone(timedelta(hours=9))


def main():
    # 실제 탐지에 쓸 것들이 번들에서 살아있는지
    import lxml.html
    import tinycss2
    import cssselect
    import requests

    doc = lxml.html.fromstring(
        '<div class="board"><span style="color:transparent">카지노 보너스</span></div>')
    el = doc.cssselect('div.board > span')[0]
    rules = tinycss2.parse_blocks_contents(el.get('style'))
    hidden = any(getattr(r, 'lower_name', '') == 'color'
                 and 'transparent' in tinycss2.serialize(r.value)
                 for r in rules if r.type == 'declaration')

    info = {
        "os": platform.platform(),
        "python": sys.version.split()[0],
        "frozen": getattr(sys, "frozen", False),
        "exe": sys.executable,
        "시각": datetime.now(KST).isoformat(),
        "한글출력": "정상 — 가나다라 ㅋㅏㅈㅣㄴㅗ",
        "lxml_cssselect": "정상",
        "tinycss2_투명감지": hidden,
        "requests": requests.__version__,
    }
    for k, v in info.items():
        print(f"{k:18s} : {v}")

    out = Path(sys.executable).parent / "probe_result.json"
    out.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n결과 파일 : {out}")
    assert hidden, "투명 텍스트 감지 실패"
    print("\n[OK] 윈도우에서 빌드·실행·한글·CSS 파싱 전부 정상")


if __name__ == "__main__":
    main()
