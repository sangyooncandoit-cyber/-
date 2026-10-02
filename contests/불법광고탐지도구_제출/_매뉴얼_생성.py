"""사용설명서와 실행·빌드 매뉴얼 PDF.

공고문 붙임1: "result.json 은 구동 파일이 위치한 폴더에 생성하는 것을 원칙으로 하며,
다른 위치에 생성하는 경우 사용설명서 첫 장에 파일별 생성 경로를 명시"
→ 우리는 원칙대로 구동 파일 폴더에 만든다. 그래도 첫 장에 적어 둔다.

공고문 붙임3: 상용 AI API 를 쓰면 서비스명·모델명·환경변수 이름을 사용설명서에 기재.
→ 쓰지 않으므로, 쓰지 않는다는 것을 첫 장에 명시한다.

  OUT_DIR  결과를 쓸 폴더. 없으면 이 폴더
"""
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OUT_DIR", HERE))
SHOT = HERE.parent / "불법광고탐지도구_첨부"
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

TOOL = "공공 누리집 숨은 광고 점검기"
EXE = "adguard.exe"
VERSION = "1.0.0"

CSS = """
@page { size: A4; margin: 16mm 16mm 14mm; }
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Noto Sans CJK KR',sans-serif;font-size:10.5pt;line-height:1.6;
  color:#111;word-break:keep-all}
h1{font-size:17pt;font-weight:700;text-align:center;letter-spacing:-.02em;margin-bottom:1mm}
.sub{text-align:center;font-size:10pt;color:#555;margin-bottom:6mm;
  padding-bottom:2.5mm;border-bottom:1pt solid #333}
h2{font-size:12.5pt;font-weight:700;margin:6mm 0 2mm;padding-bottom:1.2mm;
  border-bottom:.8pt solid #333;break-after:avoid}
h3{font-size:11pt;font-weight:700;margin:4mm 0 1.4mm;break-after:avoid}
p{margin-bottom:1.8mm;text-align:justify}
b{font-weight:700}
ul,ol{margin:1.2mm 0 2.2mm 5.5mm}
li{margin-bottom:1mm}
table{width:100%;border-collapse:collapse;margin:2mm 0 2.8mm;font-size:9.6pt}
th,td{border:.5pt solid #9A9A9A;padding:1.4mm 2mm;text-align:left;line-height:1.45;
  vertical-align:top}
th{background:#EFEFEC;font-weight:700}
thead{display:table-header-group}
tr{break-inside:avoid}
td.c,th.c{text-align:center}
code{font-family:'Noto Sans Mono CJK KR',monospace;font-size:9.2pt;
  background:#F1F1EE;padding:.3mm 1mm;border-radius:1mm}
pre{font-family:'Noto Sans Mono CJK KR',monospace;font-size:9pt;line-height:1.5;
  background:#F4F4F1;border-left:2.4pt solid #444;padding:2.2mm 3mm;margin:2mm 0 2.8mm;
  white-space:pre-wrap;word-break:break-all}
.key{margin:2mm 0 3mm;padding:2.6mm 3.2mm;border:1.2pt solid #333;background:#FAFAF6;
  line-height:1.62}
.key .lb{display:block;font-weight:700;font-size:10.8pt;margin-bottom:1.2mm}
.note{font-size:9.4pt;color:#555;line-height:1.52;margin:1mm 0 2.5mm}
figure{margin:2.5mm 0 3mm}
figure img{width:100%;border:.5pt solid #BBB}
figcaption{font-size:9pt;color:#555;margin-top:1.2mm;text-align:center}
.pb{break-before:page}
"""

# ───────────────────────────────────────────────── 사용설명서
USER = f"""
<h1>사용설명서</h1>
<div class="sub">{TOOL} · {EXE} · 버전 {VERSION}</div>

<div class="key"><span class="lb">■ 먼저 확인할 세 가지 (공고문 요구 사항)</span>
<b>1. 결과 파일 생성 경로</b><br>
<code>result.json</code> 은 <b>구동 파일({EXE})이 놓인 바로 그 폴더</b>에 만들어집니다.
다른 위치에 만들지 않습니다. 명령줄에서 <code>--out</code> 을 주면 그 폴더에 만듭니다.
추가 탐지 기능은 구현하지 않았으므로 <code>result_extra.json</code> 은 생성하지 않습니다.<br><br>
<b>2. 상용 AI API</b><br>
<b>사용하지 않습니다.</b> 따라서 기재할 API 서비스명·모델명·환경변수 이름이 없습니다.
<code>.env</code> 파일도 필요하지 않고, API KEY 교체 없이 그대로 구동됩니다.
외부 서버와 GPU 도 쓰지 않습니다.<br><br>
<b>3. 네트워크</b><br>
프로그램이 접속하는 곳은 <b>점검 대상으로 입력한 누리집 한 곳뿐</b>입니다.
수집한 내용은 외부로 보내지 않고 PC 안에서만 처리합니다.</div>

<h2>1. 실행 환경</h2>
<table>
<tr><th style="width:26%">항목</th><th>내용</th></tr>
<tr><td>운영체제</td><td>Windows 11 (64비트)</td></tr>
<tr><td>설치</td><td><b>필요 없음.</b> 파일 하나를 받아 두 번 누르면 실행됩니다.
    파이썬·런타임·라이브러리를 따로 깔지 않습니다</td></tr>
<tr><td>하드웨어</td><td>일반 사무용 PC. <b>GPU 불필요.</b> CPU·메모리만 씁니다</td></tr>
<tr><td>화면</td><td>PC 에 깔린 기본 웹브라우저를 빌려 씁니다
    (크롬·엣지·파이어폭스 무엇이든)</td></tr>
<tr><td>권한</td><td>관리자 권한 불필요. 쓰기 권한이 있는 폴더에 두면 됩니다</td></tr>
</table>

<h2>2. 실행 방법</h2>

<h3>방법 1 — 화면으로 쓰기 (평소 점검)</h3>
<ol>
<li><code>{EXE}</code> 를 두 번 누릅니다.</li>
<li>검은 창이 뜨고, 잠시 뒤 기본 브라우저에 점검 화면이 열립니다.</li>
<li>점검할 누리집 주소를 넣고 <b>[탐지 시작]</b> 을 누릅니다.</li>
<li>끝나면 결과가 화면에 나오고, 같은 폴더에 <code>result.json</code> 이 만들어집니다.</li>
<li><b>검은 창을 닫으면 프로그램이 종료됩니다.</b> 점검 중에는 닫지 마세요.</li>
</ol>
<p class="note">브라우저가 저절로 열리지 않으면, 검은 창에 적힌
<code>http://127.0.0.1:8777/</code> 같은 주소를 브라우저 주소창에 직접 넣으면 됩니다.
포트 번호는 비어 있는 것을 골라 쓰므로 실행할 때마다 다를 수 있습니다.</p>

<h3>방법 2 — 명령줄로 쓰기 (자동 점검·일괄 점검)</h3>
<pre>REM 주소를 들려서 켜면 화면이 열리면서 바로 탐지를 시작합니다
{EXE} --url https://www.example.go.kr/board/list

REM 창 없이 돌리고 끝냅니다. 결과는 result.json 으로만 남습니다
{EXE} --headless --url https://www.example.go.kr/board/list

REM 결과 파일을 다른 폴더에 만듭니다
{EXE} --headless --url https://www.example.go.kr/board/list --out D:\\점검결과</pre>
<table>
<tr><th style="width:24%">옵션</th><th>뜻</th></tr>
<tr><td><code>--url &lt;주소&gt;</code></td><td>점검을 시작할 진입 주소 하나</td></tr>
<tr><td><code>--headless</code></td><td>화면 없이 돌리고 끝냅니다.
    <code>--url</code> 과 함께 써야 합니다</td></tr>
<tr><td><code>--out &lt;폴더&gt;</code></td><td><code>result.json</code> 을 만들 폴더.
    생략하면 구동 파일이 있는 폴더</td></tr>
</table>

<h2>3. 무엇을 찾아 주는가</h2>
<p>입력한 주소에서 시작해 <b>같은 사이트의 하위 페이지, 게시글, 댓글 영역, 그리고 페이지에
삽입된 iframe 내부</b>까지 따라 들어가며 훑습니다. 사람 눈에 보이지 않게 숨겨 둔 불법광고를
네 가지 유형으로 나눠 찾습니다.</p>
<table>
<tr><th style="width:22%">유형</th><th style="width:40%">어떻게 숨긴 것인가</th><th>예</th></tr>
<tr><td><b>닮은꼴 글자 위장</b><br>HOMOGLYPH</td>
    <td>키릴·그리스·전각 문자처럼 생김새가 비슷한 글자를 섞어 필터를 피한 것.
    <b>원래 글자로 되돌려</b> 함께 보여 줍니다</td>
    <td><code>ｍｅｇａ－ＢＥＴ 첫충 30％</code><br>→ mega-BET 첫충 30%</td></tr>
<tr><td><b>자모 분해</b><br>JAMO</td>
    <td>글자를 자음·모음으로 쪼개 키워드 검색을 피한 것. <b>음절로 되붙여</b> 보여 줍니다</td>
    <td><code>ㅋㅏㅈㅣㄴㅗ</code> → 카지노</td></tr>
<tr><td><b>투명 텍스트</b><br>TRANSPARENT</td>
    <td>글자색을 배경색과 같게 하거나 투명하게 만든 것</td>
    <td>흰 배경에 흰 글자, <code>opacity:0</code></td></tr>
<tr><td><b>화면 밖 은닉</b><br>OFFSCREEN</td>
    <td>글자 크기를 0으로 하거나 화면 바깥 좌표로 밀어낸 것</td>
    <td><code>font-size:0px</code><br><code>left:-9999px</code></td></tr>
</table>
<p class="note">숨어 있다고 전부 신고하지 않습니다. 화면낭독기 전용 안내문, 접힌 메뉴,
인쇄용 숨김처럼 <b>정상적인 숨김은 걸러냅니다.</b> '숨어 있다'와 '불법광고처럼 보인다'
두 조건을 모두 만족할 때만 알려 드립니다.</p>

<h2 class="pb">4. 결과 화면 보는 법</h2>
<figure><img src="file://{{FIG1}}">
<figcaption>주소 입력 → 요약 타일 → 페이지별 검출 목록</figcaption></figure>
<table>
<tr><th style="width:24%">자리</th><th>무엇을 보여 주는가</th></tr>
<tr><td>요약 타일</td><td>검출 합계와 유형별 건수, 살펴본 페이지 수, 걸린 시간.
    <b>점검 결과를 한 줄로 보고할 때 그대로 쓰는 숫자</b>입니다</td></tr>
<tr><td>페이지별 묶음</td><td>어느 하위 페이지에 몇 건인지 묶어서 보여 줍니다.
    제목 줄의 <b>[페이지 열기]</b> 를 누르면 그 주소가 새 탭에서 열립니다</td></tr>
<tr><td>유형 단추</td><td>전체 / 미처리만 / 닮은꼴 / 자모 분해 / 투명 / 화면 밖.
    건수가 많을 때 한 유형씩 처리하면 편합니다</td></tr>
</table>

<h3>검출 한 건은 이렇게 생겼습니다</h3>
<figure><img src="file://{{FIG2}}">
<figcaption>숨긴 원문 · 되돌린 글자 · 판단 근거 · 걸린 표현 · 위치</figcaption></figure>
<table>
<tr><th style="width:24%">줄</th><th>뜻</th></tr>
<tr><td>회색 상자 윗줄</td><td>문서에 실제로 적혀 있던 <b>원문 그대로</b>입니다</td></tr>
<tr><td>원래 글자로 되돌리면</td><td>위장을 풀어 본 결과. 닮은꼴·자모 분해일 때만 나옵니다</td></tr>
<tr><td>판단 근거</td><td>왜 숨김으로 봤는지. 예: <code>font-size:0px</code>,
    <code>글자색이 배경색과 같음 (#ffffff)</code>,
    <code>FULLWIDTH 문자를 섞어 필터를 피함</code></td></tr>
<tr><td>걸린 표현</td><td>불법광고로 본 근거가 된 낱말들</td></tr>
<tr><td>위치</td><td>그 글이 문서 어디에 있는지 CSS 선택자로 적은 것.
    <b>[위치 복사]</b> 로 복사해 관리자 화면에서 찾습니다</td></tr>
</table>

<h2>5. 찾은 뒤 — 조치하고 보고하기</h2>
<ol>
<li><b>확인.</b> 판단 근거와 되돌린 글자를 보고 실제로 불법광고가 맞는지 판단합니다.</li>
<li><b>열기.</b> [페이지 열기] 로 해당 페이지를 띄웁니다.</li>
<li><b>찾기.</b> [위치 복사] 로 선택자를 복사해 기관 관리자 화면에서 그 글을 찾습니다.</li>
<li><b>삭제.</b> 기관의 게시물 관리 절차에 따라 지웁니다.</li>
<li><b>표시.</b> [처리 완료로 표시] 를 누릅니다. <b>[미처리만]</b> 을 켜면 남은 것만 보입니다.
    처리 상태는 브라우저에 저장되어 창을 닫았다 열어도 남습니다.</li>
<li><b>보고.</b> [조치 목록 내려받기] 로 CSV 를, [인쇄] 로 보고서를 만듭니다.</li>
</ol>
<p class="note">CSV 는 엑셀에서 한글이 깨지지 않도록 만들어져 있습니다. 번호·유형·페이지·위치·
검출 문구·판단 근거·처리 상태가 들어갑니다. 결재·이관·보존 문서로 그대로 쓸 수 있습니다.</p>

<h2>6. 결과 파일 (result.json)</h2>
<p>구동 파일이 있는 폴더에 <b>UTF-8(BOM 없음)</b> 로 만들어집니다. 탐지를 다시 하면
덮어씁니다. 기록을 남기려면 점검 때마다 다른 이름으로 옮겨 두거나
<code>--out</code> 으로 폴더를 나누세요.</p>
<pre>{{
  "meta": {{
    "topic": "TOPIC",
    "entry_url": "https://www.example.go.kr/board/list",
    "started_at": "2026-10-22T10:00:00+09:00",
    "finished_at": "2026-10-22T10:08:12+09:00",
    "elapsed_sec": 492.0,
    "tool_version": "{VERSION}"
  }},
  "findings": [
    {{
      "id": "f_001",
      "url": "https://www.example.go.kr/board/view?id=1024",
      "is_violation": true,
      "location": "div.notice-board &gt; span.visually-hidden",
      "evidence_text": "ㅋㅏㅈㅣㄴㅗ ㅂㅗㄴㅓㅅㅡ 코드 LUCKY7",
      "technique": "JAMO"
    }}
  ]
}}</pre>
<p class="note">검출이 한 건도 없어도 <code>findings</code> 는 빈 배열 <code>[]</code> 로
들어갑니다. iframe 안에서 찾은 건은 <code>url</code> 에 바깥 페이지 주소를 적고
<code>location</code> 에 <code>iframe[src="절대주소"] &gt;&gt;&gt; 선택자</code> 형식을 씁니다.</p>

<h2>7. 걸리는 시간</h2>
<p>한 페이지를 읽고 판정하는 데 수십 밀리초쯤 걸리고, 여덟 페이지를 동시에 가져옵니다.
대부분의 시간은 상대 서버가 응답하는 시간입니다. <b>25분이 지나면 수집을 멈추고
그때까지 찾은 것으로 결과 파일을 만듭니다.</b> 아주 큰 사이트에서도 결과 파일 없이
끝나는 일이 없게 하기 위한 장치입니다. 한 번에 최대 400쪽까지 봅니다.</p>

<h2>8. 이럴 때는</h2>
<table>
<tr><th style="width:36%">증상</th><th>확인할 것</th></tr>
<tr><td>브라우저가 안 열린다</td><td>검은 창에 적힌 <code>http://127.0.0.1:…</code> 주소를
    브라우저에 직접 넣습니다</td></tr>
<tr><td>"http 로 시작하는 주소를 넣어 주세요"</td><td>주소 앞에 <code>https://</code> 를
    붙여 주세요. 도메인만으로는 시작하지 않습니다</td></tr>
<tr><td>살펴본 페이지가 1쪽뿐이다</td><td>입력한 주소가 목록 페이지가 맞는지 확인하세요.
    로그인해야 보이는 게시판은 들어가지 못합니다</td></tr>
<tr><td>검출이 0건이다</td><td>정상입니다. 숨긴 불법광고가 없다는 뜻입니다.
    <code>result.json</code> 도 <code>findings: []</code> 로 만들어집니다</td></tr>
<tr><td>탐지가 끝나지 않는다</td><td>25분이 지나면 자동으로 멈춥니다.
    그 전에 멈추려면 검은 창을 닫으세요</td></tr>
<tr><td>창을 닫았더니 화면이 안 된다</td><td>검은 창이 프로그램 본체입니다.
    <code>{EXE}</code> 를 다시 실행하세요</td></tr>
<tr><td>백신이 막는다</td><td>단일 실행 파일로 묶은 프로그램이라 드물게 경고가 뜹니다.
    소스코드 전체를 함께 제출했으니 직접 빌드해 쓰실 수 있습니다
    (실행·빌드 매뉴얼 참고)</td></tr>
</table>

<h2>9. 이 도구가 못 하는 것</h2>
<p>정확히 적어 둡니다. <b>문서에 적혀 있는 은닉</b>을 찾습니다. 서버가 검색엔진에만 다른
문서를 내주는 방식(클로킹)이나, 자바스크립트가 실행된 뒤에야 화면에 나타나는 글자는
찾지 못합니다. 로그인이 필요한 영역, robots 로 막힌 영역도 들어가지 않습니다.
게시판에 글을 올리는 것만으로 가능한 네 가지 유형을 정확하고 빠르게 덮는 것이
이 도구의 범위입니다.</p>
"""

# ───────────────────────────────────────────── 실행·빌드 매뉴얼
BUILD = f"""
<h1>실행 · 빌드 매뉴얼</h1>
<div class="sub">{TOOL} · 소스에서 실행하고 {EXE} 를 만드는 법 · 버전 {VERSION}</div>

<h2>1. 소스 구성</h2>
<table>
<tr><th style="width:30%">파일</th><th>하는 일</th></tr>
<tr><td><code>app.py</code></td><td><b>구동 파일의 시작점.</b> 화면 서버와 명령줄 처리,
    result.json 쓰기</td></tr>
<tr><td><code>ui.html</code> · <code>app.js</code></td><td>결과 화면.
    빌드할 때 실행 파일 안에 함께 넣습니다</td></tr>
<tr><td><code>scan.py</code></td><td>수집과 판정. 하위 페이지·댓글·iframe 을 훑습니다</td></tr>
<tr><td><code>detect.py</code></td><td>탐지 규칙 네 가지</td></tr>
<tr><td><code>cascade.py</code></td><td>숨김과 관계있는 CSS 속성만 계산하는 작은 캐스케이드</td></tr>
<tr><td><code>selector.py</code></td><td>위치를 CSS 선택자로. 단일 요소를 가리키는지 검증</td></tr>
<tr><td><code>lexicon.py</code></td><td>불법광고 신호어 사전. 오탐을 막는 문지기</td></tr>
<tr><td><code>run.py</code></td><td>명령줄에서 한 번 돌려 result.json 만 만들기</td></tr>
<tr><td><code>make_fixture.py</code></td><td>정답을 아는 시험용 사이트 만들기</td></tr>
<tr><td><code>serve_fixture.py</code></td><td>그 사이트를 띄우는 서버</td></tr>
<tr><td><code>verify_result.py</code></td><td>result.json 이 표준 스키마를 지켰는지 검사</td></tr>
<tr><td><code>evaluate.py</code></td><td>탐지 결과를 정답표와 대조. 검출 수와 오탐 수</td></tr>
</table>

<h2>2. 개발 환경</h2>
<table>
<tr><th style="width:30%">항목</th><th>내용</th></tr>
<tr><td>파이썬</td><td>3.12 (3.11 이상이면 동작)</td></tr>
<tr><td>의존 패키지</td><td><code>lxml</code>, <code>cssselect</code>,
    <code>tinycss2</code>, <code>requests</code> — 네 개뿐입니다</td></tr>
<tr><td>빌드 도구</td><td><code>pyinstaller</code></td></tr>
<tr><td>외부 서비스</td><td><b>없음.</b> AI API·외부 서버·GPU·데이터베이스를 쓰지 않습니다.
    API KEY 나 <code>.env</code> 가 필요 없습니다</td></tr>
</table>
<pre>python -m pip install --upgrade pip
pip install lxml cssselect tinycss2 requests pyinstaller</pre>

<h2>3. 소스에서 바로 실행</h2>
<pre>cd tools\\adguard

REM 화면으로 실행
python app.py

REM 창 없이 한 번 돌리기
python app.py --headless --url https://www.example.go.kr/board/list

REM 화면 없이 결과 파일만 (가장 단순한 경로)
python run.py https://www.example.go.kr/board/list</pre>

<h2>4. 실행 파일 만들기</h2>
<p>Windows 에서 아래 한 줄이면 <code>dist\\{EXE}</code> 가 만들어집니다.
저장소 최상위에서 실행합니다.</p>
<pre>pyinstaller --onefile --console --clean ^
  --name adguard ^
  --paths tools/adguard ^
  --add-data "tools/adguard/ui.html;." ^
  --add-data "tools/adguard/app.js;." ^
  tools/adguard/app.py</pre>
<table>
<tr><th style="width:32%">옵션</th><th>왜 필요한가</th></tr>
<tr><td><code>--onefile</code></td><td>파일 하나로 묶습니다. 설치가 필요 없어집니다</td></tr>
<tr><td><code>--console</code></td><td>검은 창을 남깁니다. 진행 상황과 결과 파일 경로를
    찍어 주고, 창을 닫으면 종료됩니다</td></tr>
<tr><td><code>--paths tools/adguard</code></td><td>같은 폴더의 모듈들(scan·detect 등)을
    찾게 합니다</td></tr>
<tr><td><code>--add-data "…;."</code></td><td>화면 파일을 실행 파일 안에 넣습니다.
    <b>윈도우는 구분자가 세미콜론</b>입니다. 리눅스·macOS 에서는 콜론을 씁니다</td></tr>
</table>
<p class="note">리눅스나 macOS 에서 빌드한 파일은 Windows 에서 돌지 않습니다.
<b>반드시 Windows 에서 빌드해야 합니다.</b></p>

<h2>5. 빌드가 제대로 됐는지 확인하기</h2>
<p>만들었다고 끝이 아닙니다. 아래 네 단계를 거쳐야 "됐다"가 됩니다.
<b>정답을 아는 시험용 사이트를 먼저 만들고 그 자로 잽니다.</b></p>
<pre>REM ① 정답을 아는 시험용 사이트를 만든다 (4쪽, 정답 7건)
python tools/adguard/make_fixture.py

REM ② 그 사이트를 띄운다 (다른 창에서)
python tools/adguard/serve_fixture.py 8731

REM ③ 한글 출력까지 확인하며 실제로 돌린다
chcp 65001
dist\\{EXE} --headless --url http://127.0.0.1:8731/index.html

REM ④ 결과를 두 번 검사한다
python tools/adguard/verify_result.py dist/result.json
python tools/adguard/evaluate.py dist/result.json ^
  tools/adguard/fixture/answers.json http://127.0.0.1:8731</pre>
<table>
<tr><th style="width:30%">검사</th><th>통과 기준</th></tr>
<tr><td><code>verify_result.py</code></td><td>"스키마 통과". 최상위 구조, 필수 필드,
    technique 코드, id 중복, (url+location+technique) 중복,
    iframe 표기, 소요 시간 상한을 봅니다</td></tr>
<tr><td><code>evaluate.py</code></td><td><b>검출률 100% / 정확도 100%</b>
    (정답 7건 전부, 오탐 0건). location 은 문자열이 같은지가 아니라
    <b>같은 요소를 가리키는지</b>로 비교합니다</td></tr>
</table>

<h2 class="pb">6. 윈도우 PC 없이 빌드하기</h2>
<p>이 도구는 리눅스에서 개발했고 윈도우 PC 가 없었습니다. 그래서
<b>GitHub Actions 의 윈도우 러너에서 빌드하고 같은 러너에서 실행까지 시켜</b>
결과물을 내려받는 방법을 썼습니다. "될 것이다"가 아니라 "됐다"를 받아 내는 방법입니다.</p>
<p>워크플로 파일은 <code>.github/workflows/windows-build.yml</code> 에 있습니다.
하는 일은 5장과 같습니다. 빌드 → 시험용 사이트 띄우기 → 실제 실행 → 스키마 검사 →
정답표 대조 → 용량 확인 → 실행 파일 내려받기.</p>

<h3>이 경로에서 잡은 결함</h3>
<p>윈도우에서 실제로 돌려 보지 않았다면 심사 PC 에서 켜자마자 죽었을 문제입니다.</p>
<pre>UnicodeEncodeError: 'charmap' codec can't encode characters</pre>
<p>윈도우 콘솔의 기본 코드페이지가 한글을 처리하지 못해, <b>한글을 한 줄 찍는 순간
프로그램이 종료됩니다.</b> 리눅스에서는 재현되지 않습니다. <code>chcp 65001</code> 을
먼저 해도 파이썬의 출력 인코딩은 그대로라 해결되지 않습니다.
지금은 프로그램이 시작하자마자 출력 인코딩을 UTF-8 로 고정합니다
(<code>app.py</code> 의 <code>force_utf8()</code>).</p>
<p class="note">그래서 기능보다 <b>윈도우 빌드 경로 확인을 먼저</b> 했습니다.
윈도우에서 돌려 볼 수 없는 상태로 기능을 다 만든 뒤 발견했다면 늦었습니다.</p>

<h2>7. 용량을 작게 유지한 이유</h2>
<p>접수가 이메일입니다. <b>용량이 곧 제출 가능 여부</b>입니다. 그래서 브라우저 엔진을
실행 파일에 넣지 않았습니다. 대신 숨김과 관계있는 CSS 속성 약 20개만 직접 계산합니다.
화면은 PC 에 이미 깔린 브라우저를 빌려 쓰고, 서버는 파이썬 표준 라이브러리만으로
만들었습니다. 워크플로에 60MB 상한 검사를 두어 넘으면 빌드가 실패하게 해 두었습니다.</p>

<h2>8. 고칠 때 손대는 자리</h2>
<table>
<tr><th style="width:34%">무엇을 바꾸려면</th><th>어디를</th></tr>
<tr><td>광고 낱말을 더하거나 빼려면</td><td><code>lexicon.py</code> 의 목록.
    코드를 고치지 않고 낱말만 더하면 됩니다</td></tr>
<tr><td>혼동 문자를 더하려면</td><td><code>detect.py</code> 의
    <code>CONFUSABLES</code> 와 <code>SUSPECT_RANGES</code></td></tr>
<tr><td>오탐 기준을 조이거나 풀려면</td><td><code>lexicon.py</code> 의
    <code>looks_like_ad(text, threshold=2)</code></td></tr>
<tr><td>숨김 판정 속성을 늘리려면</td><td><code>cascade.py</code> 의 <code>WATCH</code></td></tr>
<tr><td>훑는 범위·시간을 바꾸려면</td><td><code>scan.py</code> 의 <code>crawl()</code>
    인자 — <code>max_pages=400</code>, <code>time_budget=25*60</code>,
    <code>workers=8</code></td></tr>
<tr><td>추가 탐지 유형을 넣으려면</td><td><code>detect.py</code> 에 규칙을 더하고
    <code>scan.py</code> 에서 <code>technique="ETC"</code> 와
    <code>extra_finding</code> 으로 담아 <code>result_extra.json</code> 을 따로 씁니다</td></tr>
</table>
<p class="note">바꾼 뒤에는 반드시 5장의 네 단계를 다시 돌리세요.
낱말 하나를 더해도 오탐이 늘면 정확도 점수가 깎입니다.</p>
"""


def crop_shots():
    """사용설명서에 넣을 화면 사진. 통짜로 넣으면 한 쪽을 다 먹는다."""
    from PIL import Image
    a = Image.open(SHOT / "01_결과화면_상단.png")
    b = Image.open(SHOT / "02_결과화면_근거.png")
    a.crop((0, 0, a.width, 1000)).save(OUT / "_m1.png")
    b.crop((0, 250, b.width, 1370)).save(OUT / "_m2.png")


def build(name, body):
    body = body.replace("{FIG1}", str(OUT / "_m1.png")).replace("{FIG2}", str(OUT / "_m2.png"))
    html = (f'<!doctype html><html lang="ko"><head><meta charset="utf-8">'
            f'<title>{name}</title><style>{CSS}</style></head><body>{body}</body></html>')
    tmp = OUT / f"_{name}.html"
    tmp.write_text(html, encoding="utf-8")
    pdf = OUT / f"{name}.pdf"
    subprocess.run([CHROME, "--headless", "--disable-gpu", "--no-sandbox",
                    "--no-pdf-header-footer", f"--print-to-pdf={pdf}",
                    f"file://{tmp}"], check=True, capture_output=True)
    import pymupdf
    print(f"{pdf.name}  {pdf.stat().st_size // 1024}KB  {pymupdf.open(pdf).page_count}쪽")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    crop_shots()
    build("5_사용설명서", USER)
    build("6_실행빌드매뉴얼", BUILD)


if __name__ == "__main__":
    main()
