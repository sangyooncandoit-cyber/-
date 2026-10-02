"""불법광고 신호어.

숨겨진 요소를 전부 신고하면 안 된다. 멀쩡한 사이트에도 숨긴 요소는 많다.
스크린리더용 안내문, 접힌 메뉴, 인쇄용 숨김 같은 것들이다.

적격평가 배점이 이렇다.
  정답 검출 개수   45점
  정답 추출 정확도 35점  ← 전체 탐지 건수 대비 정탐 비율

오탐이 늘면 두 번째가 깎인다. 그래서 '숨어 있다 + 불법광고처럼 보인다'
두 조건을 다 만족할 때만 신고한다.

닮은꼴과 자모 분해는 그 자체가 필터 회피 행위라 기준이 다르다.
정상적인 글은 키릴 문자를 섞거나 자모를 쪼개지 않는다.
"""
import re

# ── 신호어 두 등급 ────────────────────────────────────────────
# 공공 누리집에는 '충전소', '정책자금 대출', '성인 문해교육', '공무원 출장',
# '어린이 놀이터' 같은 말이 널려 있다. 이것들을 명백한 신호로 두면
# 장애인용 숨김 설명문까지 신고하게 된다. 실제로 그렇게 됐다.
# 그래서 겹치는 낱말은 한 등급 내렸다.

# 2점 — 멀쩡한 공문서에 나올 일이 거의 없는 말
STRONG = [
    "카지노", "바카라", "슬롯", "토토", "먹튀", "먹튀검증", "첫충", "매충",
    "꽁머니", "홀덤", "파워볼", "스포츠북", "라이브카지노", "보증업체",
    "메이저사이트", "안전놀이터", "사설토토", "토토사이트",
    "야동", "19금", "조건만남", "오피", "텐카페",
    "작업대출", "통장매입", "대포통장",
    "레플리카", "이미테이션", "짝퉁",
    "casino", "baccarat", "jackpot", "sportsbook",
]

# 1점 — 일상어와 겹쳐서 혼자서는 근거가 못 되는 말
WEAK = [
    "배팅", "베팅", "환전", "놀이터", "충전", "포커", "룰렛", "사다리",
    "성인", "안마", "출장", "대출", "일수", "급전", "신용불량", "개인회생",
    "명품", "위조",
    "slot", "betting", "poker",
]

# 홍보 채널 — 숨긴 글에 연락처가 있으면 광고일 확률이 매우 높다
CHANNEL = ["텔레그램", "telegram", "카톡", "kakao", "오픈채팅", "라인상담", "@"]

ALL_TERMS = STRONG + WEAK
STRONG_SET = set(STRONG)

URLISH = re.compile(r'(?:https?://|www\.)[\w.-]+|[\w-]+\.(?:com|net|org|kr|io|me|vip|xyz)\b',
                    re.I)
CODEISH = re.compile(r'\b(?:코드|추천인|가입코드|이벤트코드|code)\s*[:：]?\s*[A-Za-z0-9]{3,}',
                     re.I)


def ad_score(text):
    """불법광고다움. 0 이면 아님. 근거 목록도 돌려준다."""
    if not text or len(text.strip()) < 2:
        return 0, []
    low = text.lower()
    hits, score = [], 0
    for t in ALL_TERMS:
        if t.lower() in low:
            hits.append(t)
            score += 2 if t in STRONG_SET else 1
    for t in CHANNEL:
        if t.lower() in low:
            hits.append(t)
            score += 1
    if URLISH.search(text):
        hits.append("주소")
        score += 1
    if CODEISH.search(text):
        hits.append("코드")
        score += 2
    return score, hits


def looks_like_ad(text, threshold=2):
    """숨겨진 요소를 신고할지 결정하는 기준."""
    score, hits = ad_score(text)
    return score >= threshold, hits
