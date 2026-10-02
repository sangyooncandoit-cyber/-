"""서식4 기획서 PDF.  A4 5~10매.

개인정보(이름·연락처·이메일)는 저장소에 두지 않는다. 환경변수로 넣는다.
  APPLICANT_NAME / APPLICANT_PHONE / APPLICANT_EMAIL
  OUT_DIR  결과를 쓸 폴더. 없으면 이 폴더
넣지 않으면 빈 칸으로 찍힌다.
"""
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHOT = HERE.parent / "불법광고탐지도구_첨부"
OUT = Path(os.environ.get("OUT_DIR", HERE))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

NAME = os.environ.get("APPLICANT_NAME", "")
PHONE = os.environ.get("APPLICANT_PHONE", "")
EMAIL = os.environ.get("APPLICANT_EMAIL", "")
TITLE = "공공 누리집 숨은 광고 점검기"

CSS = """
@page { size: A4; margin: 16mm 16mm 13mm; }
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Noto Sans CJK KR','Noto Sans KR',sans-serif;font-size:10.5pt;
  line-height:1.62;color:#111;word-break:keep-all;-webkit-font-smoothing:antialiased}
h1{font-size:16pt;font-weight:700;text-align:center;letter-spacing:-.02em;margin-bottom:1mm}
.sub{text-align:center;font-size:10pt;color:#555;margin-bottom:6mm}
h2{font-size:12.5pt;font-weight:700;margin:6mm 0 2mm;padding-bottom:1.2mm;
  border-bottom:1pt solid #222;letter-spacing:-.01em}
h3{font-size:11pt;font-weight:700;margin:4mm 0 1.4mm;color:#111}
h4{font-size:10.5pt;font-weight:700;margin:2.6mm 0 1mm;color:#222;break-after:avoid}
h3{break-after:avoid}
p{margin-bottom:1.8mm;text-align:justify;orphans:2;widows:2}
b{font-weight:700}
ul,ol{margin:1.2mm 0 2mm 5.5mm}
li{margin-bottom:.9mm}
table{width:100%;border-collapse:collapse;margin:2mm 0 2.6mm;font-size:9.5pt}
th,td{border:.5pt solid #9A9A9A;padding:1.3mm 2mm;text-align:left;line-height:1.42;
  vertical-align:top}
th{background:#EFEFEC;font-weight:700}
thead{display:table-header-group}
tr{break-inside:avoid}
td.c,th.c{text-align:center}
code,.mono{font-family:'Noto Sans Mono CJK KR',monospace;font-size:9pt}
.note{font-size:9pt;color:#555;margin:1mm 0 2.5mm;line-height:1.5}
.box{margin:2mm 0 2.8mm;padding:2.2mm 3mm;background:#F4F4F1;border-left:2.4pt solid #444;
  font-size:9.8pt;line-height:1.52}
.box .lb{display:block;font-weight:700;font-size:9.2pt;color:#333;margin-bottom:.8mm}
figure{margin:2.5mm 0 3mm;text-align:center}
figure img{width:100%;border:.5pt solid #BBB}
figcaption{font-size:9pt;color:#555;margin-top:1.2mm;text-align:center}
svg{width:100%;height:auto;display:block}
.half{display:flex;gap:3mm}
.half figure{flex:1;margin:2.5mm 0 3mm}
.src{font-size:8.8pt;color:#555;line-height:1.5;margin-top:1mm}
.pb{break-before:page}
"""

# ─────────────────────────────────────────────────────────── 시스템 구조도
ARCH = """
<svg viewBox="0 0 760 330" xmlns="http://www.w3.org/2000/svg"
     font-family="Noto Sans CJK KR, sans-serif" font-size="12">
  <defs>
    <marker id="a" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"
            markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#333"/></marker>
  </defs>
  <rect x="8" y="128" width="104" height="48" rx="4" fill="#fff" stroke="#333" stroke-width="1.2"/>
  <text x="60" y="147" text-anchor="middle" font-weight="700">담당자 PC</text>
  <text x="60" y="164" text-anchor="middle" font-size="10.5" fill="#555">Windows 11</text>

  <rect x="136" y="18" width="612" height="296" rx="6" fill="#FAFAF8"
        stroke="#333" stroke-width="1.2"/>
  <text x="150" y="37" font-weight="700" font-size="12.5">탐지 도구 (설치 없는 단일 실행 파일)</text>

  <rect x="152" y="52" width="150" height="110" rx="4" fill="#fff" stroke="#666"/>
  <text x="227" y="71" text-anchor="middle" font-weight="700">① 수집부</text>
  <text x="162" y="90" font-size="10.5">· 진입 URL 에서 출발</text>
  <text x="162" y="107" font-size="10.5">· 같은 사이트 하위 페이지</text>
  <text x="162" y="124" font-size="10.5">· 게시글 · 댓글 · iframe</text>
  <text x="162" y="141" font-size="10.5">· 8개 동시 · 본문으로 형식 판별</text>
  <text x="162" y="156" font-size="10.5" fill="#555">scan.py</text>

  <rect x="318" y="52" width="178" height="178" rx="4" fill="#fff" stroke="#666"/>
  <text x="407" y="71" text-anchor="middle" font-weight="700">② 판정부</text>
  <text x="328" y="90" font-size="10.5">글자 검사 — 닮은꼴 · 자모 분해</text>
  <text x="328" y="107" font-size="10.5" fill="#555">detect.py</text>
  <text x="328" y="128" font-size="10.5">CSS 계산 — 투명 · 화면 밖</text>
  <text x="328" y="145" font-size="10.5" fill="#555">cascade.py</text>
  <text x="328" y="166" font-size="10.5">신호어 문지기 (오탐 차단)</text>
  <text x="328" y="183" font-size="10.5" fill="#555">lexicon.py</text>
  <text x="328" y="204" font-size="10.5">위치 선택자 · 유일성 검증</text>
  <text x="328" y="221" font-size="10.5" fill="#555">selector.py</text>

  <rect x="512" y="52" width="222" height="80" rx="4" fill="#fff" stroke="#666"/>
  <text x="623" y="71" text-anchor="middle" font-weight="700">③ 결과 화면</text>
  <text x="522" y="90" font-size="10.5">요약 · 페이지별 목록 · 근거 제시</text>
  <text x="522" y="107" font-size="10.5">필터 · 처리 완료 · 위치 복사</text>
  <text x="522" y="124" font-size="10.5" fill="#555">app.py · ui.html · app.js</text>

  <rect x="512" y="150" width="222" height="80" rx="4" fill="#fff" stroke="#666"/>
  <text x="623" y="169" text-anchor="middle" font-weight="700">④ 결과 파일</text>
  <text x="522" y="188" font-size="10.5">result.json (구동 파일과 같은 폴더)</text>
  <text x="522" y="205" font-size="10.5">조치 목록 CSV · 인쇄본</text>
  <text x="522" y="222" font-size="10.5" fill="#555">run.py</text>

  <rect x="152" y="248" width="582" height="50" rx="4" fill="#fff" stroke="#666"
        stroke-dasharray="4 3"/>
  <text x="162" y="267" font-weight="700" font-size="11">검증 장치 — 정답을 아는 시험용 사이트</text>
  <text x="162" y="286" font-size="10.5">make_fixture.py · serve_fixture.py · evaluate.py  —  정답표와 대조해 검출 수와 오탐 수를 센다</text>

  <line x1="112" y1="152" x2="148" y2="152" stroke="#333" marker-end="url(#a)"/>
  <line x1="302" y1="107" x2="314" y2="107" stroke="#333" marker-end="url(#a)"/>
  <line x1="496" y1="92" x2="508" y2="92" stroke="#333" marker-end="url(#a)"/>
  <line x1="496" y1="190" x2="508" y2="190" stroke="#333" marker-end="url(#a)"/>
  <text x="760" y="0" font-size="1"> </text>
</svg>
"""

# ─────────────────────────────────────────────────────────── 사용자 흐름도
FLOW = """
<svg viewBox="0 0 760 232" xmlns="http://www.w3.org/2000/svg"
     font-family="Noto Sans CJK KR, sans-serif" font-size="11">
  <defs>
    <marker id="b" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7"
            markerHeight="7" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#333"/></marker>
  </defs>
  <g stroke="#666" fill="#fff">
    <rect x="6"   y="14" width="130" height="46" rx="4"/>
    <rect x="166" y="14" width="130" height="46" rx="4"/>
    <rect x="326" y="14" width="130" height="46" rx="4"/>
    <rect x="486" y="14" width="130" height="46" rx="4"/>
    <rect x="646" y="14" width="108" height="46" rx="4"/>
  </g>
  <text x="71"  y="33" text-anchor="middle" font-weight="700">1. 주소 입력</text>
  <text x="71"  y="50" text-anchor="middle" font-size="10" fill="#555">점검할 누리집 1개</text>
  <text x="231" y="33" text-anchor="middle" font-weight="700">2. 탐지 시작</text>
  <text x="231" y="50" text-anchor="middle" font-size="10" fill="#555">훑는 페이지 수 실시간 표시</text>
  <text x="391" y="33" text-anchor="middle" font-weight="700">3. 요약 확인</text>
  <text x="391" y="50" text-anchor="middle" font-size="10" fill="#555">유형별 건수 · 걸린 시간</text>
  <text x="551" y="33" text-anchor="middle" font-weight="700">4. 건별 근거</text>
  <text x="551" y="50" text-anchor="middle" font-size="10" fill="#555">원문 · 되돌린 글자 · 판단 근거</text>
  <text x="700" y="33" text-anchor="middle" font-weight="700">5. 위치 복사</text>
  <text x="700" y="50" text-anchor="middle" font-size="10" fill="#555">선택자 한 줄</text>

  <line x1="136" y1="37" x2="162" y2="37" stroke="#333" marker-end="url(#b)"/>
  <line x1="296" y1="37" x2="322" y2="37" stroke="#333" marker-end="url(#b)"/>
  <line x1="456" y1="37" x2="482" y2="37" stroke="#333" marker-end="url(#b)"/>
  <line x1="616" y1="37" x2="642" y2="37" stroke="#333" marker-end="url(#b)"/>

  <path d="M700 60 L700 84 L71 84 L71 106" stroke="#333" fill="none" marker-end="url(#b)"/>

  <g stroke="#666" fill="#fff">
    <rect x="6"   y="108" width="178" height="46" rx="4"/>
    <rect x="214" y="108" width="178" height="46" rx="4"/>
    <rect x="422" y="108" width="150" height="46" rx="4"/>
    <rect x="602" y="108" width="152" height="46" rx="4"/>
  </g>
  <text x="95"  y="127" text-anchor="middle" font-weight="700">6. 해당 페이지 열어 삭제</text>
  <text x="95"  y="144" text-anchor="middle" font-size="10" fill="#555">기관 관리자 화면에서 조치</text>
  <text x="303" y="127" text-anchor="middle" font-weight="700">7. 처리 완료로 표시</text>
  <text x="303" y="144" text-anchor="middle" font-size="10" fill="#555">'미처리만' 으로 남은 건만</text>
  <text x="497" y="127" text-anchor="middle" font-weight="700">8. 조치 목록 저장</text>
  <text x="497" y="144" text-anchor="middle" font-size="10" fill="#555">CSV · 인쇄본으로 보고</text>
  <text x="678" y="127" text-anchor="middle" font-weight="700">9. 재점검</text>
  <text x="678" y="144" text-anchor="middle" font-size="10" fill="#555">같은 주소로 다시 실행</text>

  <line x1="184" y1="131" x2="210" y2="131" stroke="#333" marker-end="url(#b)"/>
  <line x1="392" y1="131" x2="418" y2="131" stroke="#333" marker-end="url(#b)"/>
  <line x1="572" y1="131" x2="598" y2="131" stroke="#333" marker-end="url(#b)"/>
  <path d="M678 154 L678 178 L71 178 L71 196" stroke="#333" fill="none"
        stroke-dasharray="4 3" marker-end="url(#b)"/>
  <text x="375" y="174" text-anchor="middle" font-size="10" fill="#555">
    정기 점검 — 같은 절차를 주기로 반복한다</text>
  <rect x="6" y="196" width="130" height="30" rx="4" stroke="#666" fill="#fff"
        stroke-dasharray="4 3"/>
  <text x="71" y="215" text-anchor="middle" font-size="10.5">1. 주소 입력</text>
</svg>
"""


def html():
    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<title>기획서</title><style>{CSS}</style></head><body>

<h1>기 획 서</h1>
<div class="sub">『공공 웹사이트 불법광고 탐지 도구 개발 공모전』 · 서식4</div>

<h2>1. 참가자 정보</h2>
<table>
<tr><th style="width:18%">신청자명</th><td style="width:32%">{NAME}</td>
    <th style="width:18%">연락처(휴대전화)</th><td>{PHONE}</td></tr>
<tr><th>작품명</th><td><b>{TITLE}</b></td>
    <th>연락처(이메일)</th><td>{EMAIL}</td></tr>
<tr><th>참가 형태</th><td colspan="3">개인</td></tr>
</table>

<h2>2. 개발 기획 내용</h2>

<h3>1) 개발 제안 배경 및 목적</h3>

<h4>가. 지금 현장은 공문과 사람 눈으로 막고 있다</h4>
<p>행정안전부는 2026년 1월에도 전 부처와 관련 기관에 <b>'공공 웹사이트 불법 광고 점검 및 조치
요청'</b> 공문을 보냈다. 2025년에 두 차례 같은 요청을 한 데 이어 세 번째다. 공문을 받은
기관 담당자는 자기 누리집의 게시판을 직접 열어 보고 광고로 보이는 글을 지운다.</p>
<p>문제는 이 방식이 <b>무엇을 얼마나 놓치고 있는지 알 수 없다</b>는 데 있다. 같은 보도에서
행안부 관계자는 불법·상업 광고의 규모를 묻는 질문에 이렇게 답했다.</p>
<div class="box"><span class="lb">행정안전부 관계자 (SBS Biz, 2026. 1. 22.)</span>
"광고가 유동적이고, 굉장히 가변적이라 그 숫자를 세는 게 의미가 없다."<br>
"개별 기관별로 대응하는 게 지금 단계에서는 가장 효율적이라고 판단하고 있다."</div>
<p>세지 못하면 줄었는지도 알 수 없다. 공문은 매년 나가는데 성과는 측정되지 않는다.
<b>이 기획의 출발점은 '숫자를 세는 일을 기계가 대신하게 만들자'는 것</b>이다.</p>

<h4>나. 눈으로 보는 점검으로는 잡을 수 없는 광고가 있다</h4>
<p>게시판에 그냥 올라온 광고라면 담당자가 읽고 지운다. 그러나 실제로 쓰이는 수법은
<b>사람 눈에 보이지 않게 숨기고 검색엔진에만 읽히게 하는 것</b>이다. 글자를 배경색과 같게
칠하거나, 글자 크기를 0px 로 만들거나, 화면 바깥 좌표로 밀어낸다. 담당자가 게시판을
아무리 꼼꼼히 봐도 <b>화면에 아무것도 나타나지 않으므로 발견할 수가 없다.</b></p>
<p>이 수법은 한국만의 문제가 아니다. 구글은 검색 스팸 정책에서 '숨긴 텍스트 및 링크'를
명시적으로 금지하며 그 예시로 <b>흰 배경에 흰 글자, 이미지 뒤에 글자 숨기기, CSS 로 글자를
화면 밖에 두기, 글자 크기나 투명도를 0 으로 두기</b>를 든다. 우리가 탐지 대상으로 삼은
기법과 정확히 같다. 같은 문서는 침해당한 사이트에 <b>숨긴 링크나 숨긴 글자를 심는
'콘텐츠 주입'</b>을 해킹 피해 유형으로 따로 분류한다.</p>
<p>공공 도메인이 표적이 되는 흐름도 국외에서 확인된다. 보안기업 체크포인트는 2026년 9월,
브라질 연방 부처·주의회·법원과 다수 기초자치단체의 정부 도메인이 도박 사이트로 가는
통로로 쓰인 캠페인을 공개했다. <b>공격자가 노린 것은 그 도메인이 가진 신뢰</b>였다.
우리 공공 누리집도 같은 이유로 값이 나간다.</p>

<h4>다. 공공 누리집에 광고가 붙으면 피해가 커지는 이유</h4>
<p>첫째, <b>검색 결과에서 정부가 보증한 정보처럼 보인다.</b> 앞의 보도는 구글에서
'청소년지원센터 고액 꿀알바'로 검색하면 서울시 공공기관 문의게시판에 올라온 불법 의심
광고가 그대로 노출되는 사례를 들었다. 서울시 자유게시판과 고용노동부 '칭찬합시다'
게시판에서도 상업 광고가 확인됐다.</p>
<p>둘째, <b>지우기도 쉽지 않다.</b> 글을 삭제해도 검색 결과에서 내리려면 담당자가 구글에
직접 조치를 요청해야 한다. 포털 검색 구조상 정부가 일괄 차단하기 어렵다. 그래서
<b>빨리 찾아내는 것 말고는 방법이 없다.</b></p>
<p>셋째, <b>누가 보느냐가 다르다.</b> 공공 누리집에는 학교·교육청·청소년지원기관이 많고,
그 이용자에 청소년이 포함된다. 사행산업통합감독위원회 집계로 2024년 국내 합법
사행산업 총매출은 25조 3,000억 원인데, 같은 위원회가 2022년에 실시한 제5차 불법도박
실태조사에서 <b>불법도박 시장 규모는 약 102조 7,000억 원</b>으로 추정됐다. 합법 시장의
네 배다. 한국도박문제예방치유원의 2024년 청소년 도박문제 실태조사에서는
<b>청소년의 4.3%가 이미 도박을 경험</b>했고 그 중 19.1%는 최근 6개월간 계속한 것으로
나타났다. 청소년 도박중독 상담은 <b>2024년 8,915건으로 전년 4,042건의 두 배 이상</b>이었다.
행안부 보도자료가 공모전 배경으로 든 장면도 같은 자리에 있다. 방과후학교 프로그램을
알아보려고 공공기관 누리집을 찾은 학부모가 게시판에서 도박 광고 문구를 본 일이다.</p>

<h4>라. 목적</h4>
<ol>
<li><b>보이지 않는 것을 보이게 한다.</b> 사람 눈으로는 발견할 수 없는 네 가지 은닉 기법을
기계가 찾아내 유형과 위치를 알려준다.</li>
<li><b>셀 수 있게 만든다.</b> 점검할 때마다 유형별 건수와 페이지 수가 숫자로 남는다.
기관별·시점별로 비교할 수 있으므로 공문의 효과를 측정할 수 있다.</li>
<li><b>담당자가 바로 조치하게 만든다.</b> 찾는 데서 끝내지 않고, 어느 요소인지 한 줄로
집어 주고 처리 상태를 관리하고 보고용 문서까지 내보낸다.</li>
<li><b>비용과 설치 부담을 0 으로 둔다.</b> 외부 API·서버·GPU 없이 담당자 PC 한 대에서
단일 실행 파일로 돌아간다.</li>
</ol>
<div class="src">근거 출처 — ① 행정안전부 보도자료 「공공 누리집에 숨은 불법광고, 국민이 직접
잡는다」(2026. 9. 13.) ② SBS Biz 「공공기관 검색했는데 꿀알바?…정부 홈페이지 관리
'사각지대'」(2026. 1. 22.) ③ 동아일보 「국내 사행산업 규모 25조…불법도박은
102조」(2025. 10. 29., 사행산업통합감독위원회·한국도박문제예방치유원 자료 인용)
④ Google Search Central, Spam policies for Google web search(숨긴 텍스트 및 링크,
해킹된 콘텐츠 항목) ⑤ Check Point Research, "Gaming the system: how a Chinese-speaking
actor turned Brazilian government sites into an SEO weapon"(2026. 9. 2.)</div>

<h3>2) 개발 상세 설명</h3>

<h4>가. 한 줄 요약</h4>
<p>점검할 누리집 주소 하나를 넣으면, 그 사이트의 하위 페이지·게시글·댓글과 페이지에
삽입된 iframe 내부까지 훑어 <b>숨겨진 불법광고를 찾아 유형·위치·근거를 함께 제시하고
result.json 을 생성</b>하는 Windows 단독 실행 프로그램이다.</p>

<h4>나. 활용 데이터</h4>
<table>
<tr><th style="width:26%">데이터</th><th style="width:30%">출처</th><th>쓰임</th></tr>
<tr><td>점검 대상 누리집의 HTML·CSS</td><td>실행 시 해당 사이트에서 직접 수집</td>
    <td>탐지의 원자료. 저장하지 않고 메모리에서 처리한다</td></tr>
<tr><td>유니코드 혼동 문자 대응표</td><td>직접 작성 (키릴·그리스·전각·원문자·수학 영숫자)</td>
    <td>닮은꼴 글자 위장 판정 및 원문 복원</td></tr>
<tr><td>한글 자모 조합 규칙</td><td>직접 작성 (초성 19 · 중성 21 · 종성 28)</td>
    <td>자모 분해 판정 및 음절 복원</td></tr>
<tr><td>불법광고 신호어 사전</td><td>직접 작성 (도박·성인·불법대출·홍보채널·위조품 약 60개)</td>
    <td>숨겨진 요소 가운데 광고만 가려내는 문지기</td></tr>
<tr><td>정답을 아는 시험용 사이트</td><td>직접 제작 (4쪽, 정답 7건, 함정 포함)</td>
    <td>검출 수·오탐 수 측정. 아래 '바' 항목</td></tr>
</table>
<p class="note">외부 데이터셋·학습 데이터·상용 AI API 를 쓰지 않는다. 따라서 API KEY 하드코딩,
.env 구성, 키 교체 구동에 해당하는 사항이 없다. 실행에 필요한 외부 접속은
<b>점검 대상 누리집 하나뿐</b>이다.</p>

<h4>다. 주요 기술과 선택 이유</h4>
<p>이 문제는 <b>규칙으로 완전히 풀린다.</b> 네 가지 탐지 유형은 모두 "문서에 그렇게 적혀
있는가"로 판정된다. 키릴 문자가 섞였는지, 자모가 쪼개졌는지, 계산된 색이 배경과 같은지,
좌표가 화면 밖인지는 모두 결정적인 값이다. 추론이 필요한 구간이 없다. 그래서 다음과 같이
설계했다.</p>
<table>
<tr><th style="width:24%">선택</th><th style="width:38%">내용</th><th>그렇게 한 이유</th></tr>
<tr><td>규칙 엔진 (AI 모델 미사용)</td><td>파이썬 순수 구현 + 표준 라이브러리 중심</td>
    <td>빠르고, 결과가 매번 같고, 왜 그렇게 판정했는지 설명할 수 있다. 심사 PC 에 GPU 가
    없어도 제약이 없다</td></tr>
<tr><td>브라우저를 넣지 않음</td><td>숨김과 관계있는 CSS 속성 약 20개만 직접 계산.
    명시도·!important·상속·@media 처리</td>
    <td>브라우저를 포함하면 실행 파일이 200MB 를 넘어 이메일 제출이 어렵고, 페이지마다
    렌더링을 기다려 검출 시간이 길어진다</td></tr>
<tr><td>외부 서버·API 없음</td><td>담당자 PC 안에서 전부 끝난다</td>
    <td>운영 비용이 0 원이고, 외부 서비스 장애가 점검을 멈추지 못한다. 점검 대상 자료가
    기관 밖으로 나가지 않는다</td></tr>
<tr><td>동시 수집</td><td>8개 요청 동시 처리, 시간 예산 25분에서 끊음</td>
    <td>타임아웃 상한 30분 안에 반드시 결과 파일이 생성되도록 보장</td></tr>
</table>

<h4>라. 시스템 구조</h4>
<figure>{ARCH}<figcaption>그림 1. 시스템 구조 — 담당자 PC 한 대 안에서 수집·판정·출력이
끝난다. 외부 접속은 점검 대상 누리집뿐이다.</figcaption></figure>

<h4>마. 탐지 규칙 네 가지</h4>
<table>
<tr><th style="width:15%">유형 코드</th><th style="width:40%">판정 방법</th><th>실제 검출 예</th></tr>
<tr><td><b>HOMOGLYPH</b><br>닮은꼴 글자 위장</td>
    <td>글자마다 유니코드 영역을 본다. 키릴·그리스·전각·원문자·수학 영숫자가 라틴/숫자
    자리에 섞여 있으면 위장으로 본다. 대응표로 <b>원문을 복원해</b> 함께 제시한다</td>
    <td class="mono">ｍｅｇａ－ＢＥＴ 첫충 30％<br>→ mega-BET 첫충 30%</td></tr>
<tr><td><b>JAMO</b><br>자모 분해</td>
    <td>호환 자모(ㄱ–ㅎ, ㅏ–ㅣ)가 이어진 구간을 찾아 초성·중성·종성 규칙으로 음절을
    되붙인다. 다음 글자가 또 초성+중성이면 받침이 아니라 다음 음절의 초성으로 처리한다</td>
    <td class="mono">ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ<br>→ 카지노 보너스</td></tr>
<tr><td><b>TRANSPARENT</b><br>투명 텍스트</td>
    <td>요소의 계산된 글자색과 실제 배경색을 각각 구해 거리를 잰다. opacity:0,
    color:transparent, 알파 0, 배경과 같은 색을 모두 같은 자리에서 잡는다. 배경은
    상위 요소를 거슬러 올라가며 찾는다</td>
    <td class="mono">color:#fff / 배경 #fff<br>opacity:0</td></tr>
<tr><td><b>OFFSCREEN</b><br>화면 밖 은닉</td>
    <td>font-size 0~1px, display:none, visibility:hidden, left/top −9999px 류,
    clip/clip-path 로 0 크기, width·height 0 을 계산값으로 확인한다</td>
    <td class="mono">font-size:0px<br>position:absolute;left:-9999px</td></tr>
</table>

<h4>바. 오탐을 막는 문지기</h4>
<p>멀쩡한 누리집에도 숨긴 요소는 많다. 화면낭독기 전용 안내문, 접힌 메뉴, 인쇄용 숨김
같은 것이다. 구글도 같은 문서에서 아코디언·슬라이더·툴팁·화면낭독기 전용 텍스트는
위반이 아니라고 명시한다. <b>이것들을 전부 신고하면 '정답 추출 정확도'가 깎인다.</b></p>
<p>그래서 투명·화면 밖 두 유형은 <b>'숨어 있다'와 '불법광고처럼 보인다' 두 조건을 모두
만족할 때만</b> 신고한다. 뒤 조건은 신호어 사전으로 점수를 매겨 판단한다. 도박·성인·불법
대출 낱말은 2점, 홍보 채널·주소·가입코드는 1~2점이고 합이 기준을 넘어야 통과한다.
닮은꼴과 자모 분해는 그 행위 자체가 필터 회피라 이 문지기를 거치지 않는다.
정상적인 글은 키릴 문자를 섞거나 자모를 쪼개지 않는다.</p>

<h4>사. 위치를 어떻게 적는가</h4>
<p>채점 단위가 <b>(url + location + technique)</b> 조합이고, 선택자가 두 곳 이상을 가리키면
오답이 된다. 그래서 선택자를 만든 뒤 <b>그 선택자로 문서를 다시 조회해 정확히 하나만
잡히는지 검증</b>한다. 얕은 경로부터 시도해 유일해질 때까지 상위 요소를 덧붙이고,
끝까지 좁혀지지 않으면 클래스를 유지한 채 <code>:nth-of-type(n)</code> 을 붙인다.
iframe 안에서 찾은 건은 <b>바깥 페이지 주소</b>를 url 로 적고 location 에
<code>iframe[src="절대주소"] &gt;&gt;&gt; 선택자</code> 형식을 쓴다.</p>
<div class="box"><span class="lb">실제 생성 예</span>
<span class="mono">url: http://.../index.html<br>
location: iframe[src="http://.../widget.html"] &gt;&gt;&gt; span.tiny<br>
technique: OFFSCREEN</span></div>

<h4>아. 결과 파일</h4>
<p>구동 파일과 같은 폴더에 <b>result.json</b>(UTF-8, BOM 없음)을 만든다. 최상위는 meta 와
findings 두 키이며, 검출이 없어도 findings 는 빈 배열로 포함한다. 화면 표시에만 쓰는
값은 전부 별도 키로 분리해 <b>결과 파일에는 규정된 필드만 들어가도록</b> 했다. 한 요소에
두 기법이 겹치면 기법별로 객체를 따로 만들고, 같은 요소 안에 같은 기법 문자열이 여러 개면
1건으로 묶는다.</p>

<h4>자. 결과 확인·안내·관리 기능과 화면 구성</h4>
<p>탐지 결과를 <b>업무로 이어지게</b> 만드는 것을 화면 설계의 목표로 삼았다. 담당자가
화면에서 하는 일은 '찾았다'를 보는 것이 아니라 '지웠다'까지 가는 것이다.</p>
<figure>{FLOW}<figcaption>그림 2. 사용자 흐름 — 주소 입력에서 조치·보고·재점검까지
한 화면 안에서 끝난다.</figcaption></figure>
<table>
<tr><th style="width:22%">화면 구성</th><th>담당자가 얻는 것</th></tr>
<tr><td>요약 타일</td><td>검출 합계, 유형별 건수, 살펴본 페이지 수, 걸린 시간.
    점검 결과를 한 줄로 보고할 수 있는 숫자가 바로 나온다</td></tr>
<tr><td>페이지별 묶음</td><td>어느 하위 페이지에 몇 건인지. 페이지 단위로 조치하는
    실제 업무 순서와 같다. '페이지 열기'로 해당 주소를 바로 띄운다</td></tr>
<tr><td>건별 근거</td><td>① 숨긴 원문 그대로 ② 원래 글자로 되돌린 결과
    ③ 판단 근거(예: 'FULLWIDTH 문자를 섞어 필터를 피함', 'font-size:0px')
    ④ 걸린 표현 ⑤ 위치 선택자. <b>왜 이것이 불법광고인지를 담당자가 직접 확인</b>할 수
    있어야 삭제 결정을 내릴 수 있다</td></tr>
<tr><td>유형 필터 · 미처리만</td><td>건수가 많을 때 한 유형씩 처리한다.
    처리한 건은 '처리 완료'로 표시되어 목록에서 빠지므로 어디까지 했는지 잃지 않는다</td></tr>
<tr><td>위치 복사</td><td>선택자를 한 번에 복사해 기관 관리자 화면에서 바로 찾는다</td></tr>
<tr><td>조치 목록 내려받기 · 인쇄</td><td>CSV(엑셀에서 한글이 깨지지 않도록 BOM 포함)와
    인쇄본. 결재·이관·보존 문서로 그대로 쓴다</td></tr>
</table>
<figure><img src="file://{OUT}/_fig3.png">
<figcaption>그림 3. 결과 화면 — 주소 입력, 요약 타일, 페이지별 검출 목록</figcaption></figure>
<figure><img src="file://{OUT}/_fig4.png">
<figcaption>그림 4. 건별 근거 — 숨긴 원문, 되돌린 글자, 판단 근거, 걸린 표현, 위치</figcaption></figure>

<h4>차. 정확도를 어떻게 확인했는가</h4>
<p>평가용 테스트 사이트는 공개되지 않는다. 그래서 <b>정답을 미리 아는 시험용 사이트를
먼저 만들고</b> 도구를 그 자로 쟀다. 공고문 붙임1의 기법 설명과 붙임4의 작성 예시를
근거로 4쪽짜리 사이트를 구성하고 정답표를 함께 적었다. 네 유형을 모두 넣고,
게시글 본문·목록·댓글·iframe 내부에 흩어 두었다. 함정도 같이 심었다. 화면낭독기 전용
<code>.sr-only</code> 안내문과 접힌 메뉴다. 둘 다 숨어 있지만 불법광고가 아니다.</p>
<table>
<tr><th class="c" style="width:34%">항목</th><th class="c" style="width:22%">결과</th><th>비고</th></tr>
<tr><td>정답 7건 중 검출</td><td class="c"><b>7건 (100%)</b></td>
    <td>네 유형 모두 포함. iframe 내부 1건 포함</td></tr>
<tr><td>오탐</td><td class="c"><b>0건</b></td><td>함정 2건을 모두 통과시키지 않음</td></tr>
<tr><td>위치 선택자 유일성</td><td class="c"><b>7건 전부 단일 요소</b></td>
    <td>생성 후 재조회로 검증</td></tr>
<tr><td>결과 파일 스키마</td><td class="c"><b>규정 필드만 포함</b></td>
    <td>화면 전용 값은 분리</td></tr>
</table>
<p>개발 중 이 검증으로 두 가지 결함을 잡았다. 하나는 게시글 주소에 쿼리가 붙으면 서버가
HTML 이 아닌 형식으로 응답하는 경우가 있어 <b>페이지 4쪽 중 3쪽을 통째로 놓치고 있던
것</b>이다. 본문 앞머리를 보고 HTML 이면 읽도록 고쳤다. 다른 하나는 iframe 안에서 찾은
건의 url 을 iframe 문서 주소로 적고 있던 것이다. 채점이 (url + location + technique)
조합이므로 그대로 뒀으면 해당 건이 통째로 오답이 됐다.</p>

<h4>카. 실행 환경 검증</h4>
<p>개발은 리눅스에서 했으므로 <b>Windows 에서 실제로 켜지는지를 먼저 확인</b>하고 기능
개발을 시작했다. 윈도우 러너에서 단일 실행 파일로 빌드하고 같은 환경에서 실행까지
확인했다. 이 과정에서 <b>한글을 출력하는 순간 프로그램이 죽는 결함</b>을 발견했다.
윈도우 콘솔 기본 코드페이지가 한글을 처리하지 못해 일어나는 문제로, 리눅스에서는
재현되지 않는다. 기능을 다 만든 뒤에 발견했다면 심사 PC 에서 켜자마자 종료됐을 것이다.
현재는 프로그램 시작 시 출력 인코딩을 UTF-8 로 고정해 해결했다.</p>

<h3>3) 활용방안 및 기대효과</h3>

<h4>가. 실제 행정서비스에서의 활용 방법</h4>
<p>이 도구는 <b>지금 이미 돌아가고 있는 절차에 그대로 끼워 넣도록</b> 설계했다. 행안부가
공문을 보내면 기관 담당자가 자기 누리집을 점검하는 흐름은 바꾸지 않는다. 담당자가
'눈으로 보는' 자리에 '도구를 돌리는' 일을 넣을 뿐이다.</p>
<table>
<tr><th style="width:20%">단계</th><th style="width:40%">지금</th><th>도구 도입 후</th></tr>
<tr><td>점검 요청</td><td>행안부 공문 발송</td><td>공문에 도구 배포본과 사용설명서 동봉</td></tr>
<tr><td>점검</td><td>담당자가 게시판을 눈으로 확인. 숨긴 광고는 발견 불가</td>
    <td>누리집 주소 하나를 넣고 실행. 하위 페이지·댓글·iframe 까지 자동</td></tr>
<tr><td>조치</td><td>발견한 글을 삭제</td>
    <td>건별 근거를 확인하고 위치를 복사해 삭제. 처리 완료로 표시</td></tr>
<tr><td>보고</td><td>조치했다는 회신</td>
    <td>유형별 건수·페이지 수·처리 현황이 담긴 CSV 와 인쇄본 첨부</td></tr>
<tr><td>사후 관리</td><td>다음 공문까지 공백</td>
    <td>같은 주소로 주기 재실행. 기관·시점별 수치 비교</td></tr>
</table>

<h4>나. 확산 가능성</h4>
<ul>
<li><b>설치가 필요 없다.</b> 단일 실행 파일 하나다. 기관 PC 에 설치 권한이 없어도,
보안 정책으로 프로그램 설치가 제한돼도 실행할 수 있다.</li>
<li><b>비용이 들지 않는다.</b> 외부 API·서버·GPU·라이선스가 없다. 기관 수가 늘어도
운영비가 늘지 않는다. 도입 심의에서 예산 항목이 생기지 않는다.</li>
<li><b>자료가 기관 밖으로 나가지 않는다.</b> 수집한 페이지를 외부로 전송하지 않고
메모리에서 처리한다. 공공기관의 외부 전송 제약에 걸리지 않는다.</li>
<li><b>배우는 데 시간이 들지 않는다.</b> 주소를 넣고 버튼을 누르면 끝이다.
연초 인사이동으로 담당자가 바뀌어도 인계 부담이 거의 없다.</li>
</ul>

<h4>다. 타 기관·부문과의 연계</h4>
<p>생성되는 result.json 은 공고문이 정한 표준 스키마를 그대로 따르므로 <b>기관별 결과를
모아 집계하는 상위 시스템을 붙이기 쉽다.</b> 기관이 결과 파일만 제출하면 소관 부처는
유형별·기관별 건수를 자동으로 합산할 수 있다. 행안부가 수행하는 공공 웹사이트 품질관리
체계의 점검 항목으로 편입하면 별도 조사 없이 수치가 쌓인다.</p>
<p>검출된 건은 그 자체가 신고 자료가 된다. 복원된 원문, 위치, 유형, 수집 시각이 함께
남으므로 방송미디어통신심의위원회 통신심의 요청이나 수사 의뢰에 쓸 수 있는 형태다.</p>

<h4>라. 실증 및 운영 계획</h4>
<ol>
<li><b>1단계 — 소수 기관 시범.</b> 게시판 규모가 다른 기관 몇 곳에서 돌려 검출 건수와
소요 시간을 수집한다. 오탐이 나온 건은 신호어 사전과 문지기 기준에 반영한다.</li>
<li><b>2단계 — 점검 주기 결정.</b> 시범 결과의 재유입 속도를 보고 주기를 정한다.
도구 실행 비용이 0 이므로 주기를 짧게 가져가도 부담이 없다.</li>
<li><b>3단계 — 전 기관 배포.</b> 공문에 실행 파일과 사용설명서를 동봉한다.
결과 파일 제출을 함께 요청하면 현황 집계가 시작된다.</li>
<li><b>지속 관리 — 사전 갱신.</b> 은닉 수법과 광고 문구는 계속 바뀐다. 신호어 사전과
혼동 문자 대응표는 코드를 고치지 않고 목록만 갱신하면 되도록 분리해 두었다.</li>
</ol>

<h4>마. 기대효과</h4>
<table>
<tr><th style="width:24%">구분</th><th>내용</th></tr>
<tr><td>행정 효율</td><td>담당자가 게시판을 넘겨 보던 시간이 실행 한 번으로 바뀐다.
    더 중요하게는, <b>눈으로는 애초에 찾을 수 없던 네 가지 은닉 유형이 점검 범위 안으로
    들어온다.</b> 하위 페이지·댓글·iframe 내부까지 빠짐없이 훑는다</td></tr>
<tr><td>측정 가능성</td><td>"숫자를 세는 게 의미가 없다"던 현황이 <b>유형별·기관별·시점별
    수치</b>로 바뀐다. 공문 발송 전후를 비교할 수 있고, 어느 기관이 취약한지 보인다.
    정책 효과를 근거로 말할 수 있게 된다</td></tr>
<tr><td>국민 편익</td><td>검색 결과에서 공공기관 이름을 달고 노출되던 도박·성인·불법대출
    광고가 줄어든다. 특히 학교·교육청·청소년기관 누리집에서 청소년이 도박 광고에
    노출되는 경로를 끊는다</td></tr>
<tr><td>신뢰 회복</td><td>공공 도메인이 가진 신뢰가 불법 사업자의 홍보 자산으로 쓰이는
    구조를 끊는다. 국외에서 확인된 공공 도메인 표적화 흐름에 대한 대비이기도 하다</td></tr>
<tr><td>경제적 효과</td><td>도입·운영 비용이 0 원이다. 기관 수에 비례해 늘어나는 비용이
    없으므로, 전 기관 배포 시에도 추가 예산이 필요하지 않다</td></tr>
</table>

<h4>바. 한계와 보완 방향</h4>
<p>과장하지 않기 위해 분명히 적는다. 이 도구는 <b>문서에 적혀 있는 은닉</b>을 잡는다.
서버가 검색엔진에만 다른 문서를 내주는 방식(클로킹)이나 자바스크립트가 실행된 뒤에야
나타나는 글자는 현재 구조로는 잡지 못한다. 앞서 든 브라질 사례가 바로 서버단 방식이었다.
다만 이런 수법은 서버 침해를 전제하므로 보안 점검의 영역이고, 게시판에 글을 올리는 것만으로
가능한 네 가지 유형과는 난이도가 다르다. <b>지금 공공 누리집에서 실제로 벌어지는 일은
후자이며, 그 영역을 정확하고 빠르게, 비용 없이 덮는 것</b>을 이 도구의 범위로 잡았다.
자바스크립트 렌더링은 선택 기능으로 분리해 두면 검출 시간을 희생하지 않고 확장할 수 있다.</p>

<h2>3. 제출물 및 실행 방법 요약</h2>
<p class="note">서식4 유의사항의 "제시한 목차 외 추가 내용이 있을 경우 별도의 목차를
추가"에 따라, 적격평가 구동에 필요한 사항을 한 쪽으로 정리한다. 상세는 사용설명서를
따른다.</p>
<table>
<tr><th style="width:26%">구분</th><th>내용</th></tr>
<tr><td>구동 파일</td><td>Windows 11 단일 실행 파일 1개. 설치·런타임 설치 불필요</td></tr>
<tr><td>실행 방법</td><td>실행 파일을 켜면 기본 브라우저에 화면이 열린다.
    점검할 주소를 넣고 '탐지 시작'을 누른다. 화면 없이 돌릴 때는
    <code>--headless --url &lt;주소&gt;</code> 로 실행한다</td></tr>
<tr><td>결과 파일 생성 위치</td><td><b>구동 파일이 있는 폴더</b>에 <code>result.json</code>
    (UTF-8, BOM 없음). 별도 지정 경로 없음</td></tr>
<tr><td>상용 AI API</td><td><b>사용하지 않음.</b> API KEY·.env·외부 서버·GPU 모두 해당 없음.
    외부 접속은 점검 대상 누리집뿐</td></tr>
<tr><td>소요 시간 제어</td><td>시간 예산 25분에서 수집을 끊고 결과를 쓴다.
    타임아웃 상한 30분을 넘기지 않는다</td></tr>
<tr><td>개발자료</td><td>소스코드 전체, 실행·빌드 매뉴얼, 사용설명서</td></tr>
</table>

</body></html>"""


def crop_shots():
    """결과 화면 원본에서 기획서에 쓸 부분만 잘라낸다. 통짜로 넣으면 한 쪽을 다 먹는다."""
    from PIL import Image
    a = Image.open(SHOT / "01_결과화면_상단.png")
    b = Image.open(SHOT / "02_결과화면_근거.png")
    a.crop((0, 0, a.width, 1000)).save(OUT / "_fig3.png")       # 입력 · 요약 · 필터
    b.crop((0, 250, b.width, 1370)).save(OUT / "_fig4.png")     # 근거 두 건


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    crop_shots()
    out_html = OUT / "_기획서.html"
    out_pdf = OUT / "4_기획서.pdf"
    out_html.write_text(html(), encoding="utf-8")
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={out_pdf}",
                    f"file://{out_html}"], check=True,
                   capture_output=True)
    import pymupdf
    print(f"{out_pdf.name}  {out_pdf.stat().st_size // 1024}KB  "
          f"{pymupdf.open(out_pdf).page_count}쪽")


if __name__ == "__main__":
    main()
