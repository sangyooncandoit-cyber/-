"""탐지 규칙 회귀 시험.

여기 있는 것은 전부 실제로 한 번 틀렸던 자리다.
실제 공공 누리집(mois.go.kr)을 훑어 보고 나온 오탐을 그대로 옮겨 적었다.

정확도 35점은 '전체 탐지 건수 대비 정탐 비율'이다.
오탐 하나가 정답 하나와 같은 무게로 깎는다. 그래서 '놓치지 않는가' 만큼
'엉뚱한 것을 신고하지 않는가' 를 함께 지킨다.

  python test_detect.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from winout import force_utf8                                   # noqa: E402
from detect import find_homoglyph, find_jamo                    # noqa: E402
from lexicon import looks_like_ad                               # noqa: E402

# ── 닮은꼴 글자 위장 ─────────────────────────────────────────
HOMOGLYPH = [
    # (글, 잡아야 하나, 왜)
    ("ｍｅｇａ－ＢＥＴ 첫충 30％ 지급", True, "전각 영문으로 낱말을 만듦"),
    ("ＢＥＴ365 가입", True, "전각 영문"),
    ("саsino 보너스", True, "키릴 с, а 를 라틴 자리에 끼움"),
    ("３０％ 첫충 지급", True, "전각 숫자"),

    ("ⓒ 한국정책방송원 무단전재 및 재배포 금지", False,
     "저작권 기호. 실제 mois.go.kr 뉴스 자막에서 오탐 8건을 낸 자리"),
    ("① 신청 ② 접수 ③ 심사 ④ 결과 발표", False, "공문서에 늘 쓰는 번호"),
    ("전년 대비 30％ 증가했습니다", False, "전각 퍼센트 기호 한 개"),
    ("（서울）＝연합뉴스", False, "전각 괄호"),
    ("측정값은 100Ω 입니다", False, "단위 기호"),
    ("두께 μm 단위로 측정", False, "단위 기호"),
    ("α선과 β선의 차이", False, "그리스 문자를 기호로 씀"),
    ("일반적인 한국어 문장입니다.", False, "아무것도 없음"),
]

# ── 자모 분해 ───────────────────────────────────────────────
JAMO = [
    ("ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ 코드 LUCKY7", True, "음절을 자모로 쪼갬"),
    ("ㅋㅋㅋ 재밌네요", False, "웃음 표현"),
    ("ㅠㅠ 아쉽습니다", False, "감정 표현"),
    ("ㄱㄴㄷ 순서로 정렬", False, "자음만 나열"),
    ("자음과 모음을 배웁니다", False, "그냥 글"),
]

# ── 광고 신호어 문지기 ───────────────────────────────────────
# 숨어 있는 요소를 신고할지 정하는 문이다. 공공 누리집에는 장애인용
# 숨김 설명문이 많아서, 흔한 낱말 하나로 열리면 안 된다.
LEXICON = [
    ("무료 슬롯 체험 바로가기 jackpot-win.vip", True, "도박 사이트 유도"),
    ("바카라 환전 보증업체 안내", True, "명백한 도박 용어"),
    ("먹튀검증 안전놀이터 상담 텔레그램 @promo_777", True, "도박 + 연락 채널"),
    ("홀덤 포커 가입코드 ABC123", True, "도박 + 가입코드"),
    ("카지노 보너스 코드 LUCKY7", True, "도박 + 코드"),

    ("구분, 계, 공공용시설, 교통시설, 관광·체육시설, 상업시설, "
     "주유소·충전소, 기타로 구분한 장소별 현황을 설명하는 표입니다.", False,
     "장애인용 표 설명문. '충전소' 때문에 실제로 오탐이 났던 자리"),
    ("정책자금 대출 상담 안내", False, "'대출' 은 공공 누리집에 흔하다"),
    ("성인 문해교육 수강생 모집", False, "'성인' 은 교육 안내에 흔하다"),
    ("공무원 국외 출장 결과 보고서", False, "'출장' 은 공문서에 흔하다"),
    ("어린이 놀이터 안전점검 결과", False, "'놀이터' 는 시설 안내에 흔하다"),
    ("전기차 충전소 설치 현황", False, "'충전' 은 시설 안내에 흔하다"),
    ("여행자 환전 안내 및 유의사항", False, "'환전' 은 금융 안내에 흔하다"),
    ("본문 바로가기 메뉴 바로가기", False, "건너뛰기 링크"),
]


def run(name, cases, fn):
    bad = []
    for text, want, why in cases:
        got = fn(text)
        if got != want:
            bad.append((text, want, got, why))
    mark = "통과" if not bad else f"실패 {len(bad)}건"
    print(f"{name:14s} {len(cases):2d}건 중 {len(cases) - len(bad):2d}건 맞음  — {mark}")
    for text, want, got, why in bad:
        print(f"    기대 {want} / 결과 {got}  ({why})")
        print(f"      {text[:70]}")
    return not bad


def main():
    force_utf8()
    ok = True
    ok &= run("닮은꼴 위장", HOMOGLYPH, lambda t: find_homoglyph(t) is not None)
    ok &= run("자모 분해", JAMO, lambda t: find_jamo(t) is not None)
    ok &= run("신호어 문지기", LEXICON,
              lambda t: looks_like_ad(t, threshold=2)[0])
    print()
    print("전부 통과" if ok else "실패한 항목이 있다")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
