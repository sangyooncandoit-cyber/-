"""서식1 참가신청서 · 서식2 참가 서약서 · 서식3 개인정보 수집·이용 동의서.

주최 서식을 그대로 옮겨 채운 PDF 다. 폰에서 한글 파일을 고칠 수 없어서 PDF 로 만든다.
공고문은 이메일 접수만 요구하고 HWP 로 내라는 말은 없다.

개인정보와 서명은 저장소에 두지 않는다. 전부 바깥에서 받는다.
  APPLICANT_NAME  APPLICANT_PHONE  APPLICANT_EMAIL  APPLICANT_ADDR
  SIGN_PNG   서명 그림 경로 (본인 손글씨를 찍어 다듬은 것)
  OUT_DIR    결과를 쓸 폴더. 없으면 이 폴더
  SIGN_DATE  서명 날짜 'YYYY-MM-DD'. 없으면 오늘
"""
import datetime as dt
import os
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path(os.environ.get("OUT_DIR", HERE))
CHROME = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"

NAME = os.environ.get("APPLICANT_NAME", "")
PHONE = os.environ.get("APPLICANT_PHONE", "")
EMAIL = os.environ.get("APPLICANT_EMAIL", "")
ADDR = os.environ.get("APPLICANT_ADDR", "")
SIGN = os.environ.get("SIGN_PNG", "")
TITLE = "공공 누리집 숨은 광고 점검기"

_d = os.environ.get("SIGN_DATE")
D = dt.date.fromisoformat(_d) if _d else dt.date.today()
DATE = f"{D.year}년 {D.month}월 {D.day}일"

CSS = """
@page{size:A4;margin:16mm 16mm 14mm}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Noto Sans CJK KR',sans-serif;font-size:10.5pt;line-height:1.5;
  color:#111;word-break:keep-all}
.form{font-size:10pt;font-weight:700;border:.8pt solid #333;display:inline-block;
  padding:.8mm 2.4mm;margin-bottom:3mm}
h1{font-size:17pt;font-weight:700;text-align:center;letter-spacing:.42em;
  text-indent:.42em;margin-bottom:2mm}
.sub{text-align:center;font-size:10.5pt;color:#333;margin-bottom:6mm}
table{width:100%;border-collapse:collapse;margin-bottom:2mm}
th,td{border:.6pt solid #666;padding:1.7mm 2.4mm;vertical-align:middle;line-height:1.45}
th{background:#EFEFEC;font-weight:700;text-align:center}
td.v{font-weight:500}
.na{color:#777}
.box{border:.6pt solid #666;padding:2.6mm 3mm;line-height:1.6;margin-bottom:2mm;
  font-size:10pt}
ol.sv{margin:2mm 0 0 6mm;font-size:10pt;line-height:1.6}
ol.sv li{margin-bottom:1.4mm}
.agree{margin:3mm 0 1.5mm;line-height:1.6}
.signblk{margin-top:7mm;text-align:center;line-height:2.1}
.signrow{display:inline-flex;align-items:center;gap:2.5mm;white-space:nowrap}
.sig{height:16mm;margin-bottom:-5.5mm}
.to{margin-top:10mm;font-weight:700;font-size:11.5pt;letter-spacing:.05em}
.att{margin-top:8mm;font-size:10pt;line-height:1.6}
.att b{display:block;margin-bottom:.8mm}
tr{break-inside:avoid}
.small{font-size:9.6pt;line-height:1.55}
"""

ABSTRACT = """점검할 공공 누리집 주소 하나를 넣으면, 그 사이트의 하위 페이지·게시글·댓글과
페이지에 삽입된 iframe 내부까지 훑어 <b>사람 눈에 보이지 않게 숨겨진 불법광고를 찾아내는</b>
윈도우용 프로그램입니다.<br><br>
지금 공공기관은 행안부 공문을 받아 담당자가 게시판을 눈으로 확인하는 방식으로 대응합니다.
그런데 실제로 쓰이는 수법은 글자를 배경색과 같게 칠하거나 크기를 0px 로 만들거나 화면
바깥으로 밀어내는 것이어서, 화면에 아무것도 나타나지 않으므로 아무리 꼼꼼히 봐도 찾을 수
없습니다. 이 도구는 그 네 가지 은닉 기법을 기계가 찾아 <b>유형·위치·판단 근거를 함께</b>
보여 주고, 담당자가 바로 지울 수 있도록 위치를 한 줄로 집어 줍니다.<br><br>
찾는 데서 끝내지 않습니다. 처리한 건을 표시해 남은 것만 보고, 조치 목록을 CSV 와 인쇄본으로
내보내 보고 문서로 씁니다. 점검할 때마다 유형별 건수가 숫자로 남으므로
<b>"숫자를 세는 게 의미가 없다"던 현황을 기관별·시점별로 비교할 수 있게 됩니다.</b><br><br>
외부 API·서버·GPU 를 쓰지 않습니다. 설치가 필요 없는 단일 실행 파일 하나로 담당자 PC
한 대에서 끝나며, 도입·운영 비용이 0원입니다."""

TECH = """<b>활용 데이터</b> — 점검 대상 누리집의 HTML·CSS(실행 시 직접 수집, 저장하지 않음),
직접 작성한 유니코드 혼동 문자 대응표(키릴·그리스·전각·원문자·수학 영숫자), 한글 자모 조합
규칙(초성 19·중성 21·종성 28), 불법광고 신호어 사전(도박·성인·불법대출·홍보채널·위조품 약
60개), 정답을 아는 자체 제작 시험용 사이트(4쪽·정답 7건). 외부 데이터셋과 학습 데이터는
쓰지 않습니다.<br><br>
<b>주요 기술</b> — 파이썬 규칙 엔진. ① 유니코드 영역 판별로 닮은꼴 글자 위장을 잡고 원문을
복원합니다. ② 자모 재결합으로 쪼갠 음절을 되붙입니다. ③ 숨김과 관계있는 CSS 속성 약 20개만
직접 계산하는 캐스케이드 구현으로(명시도·!important·상속·@media 처리) 투명 텍스트와 화면 밖
은닉을 판정합니다. ④ 신호어 점수제 문지기로 화면낭독기 전용 텍스트 같은 정상 요소를 걸러
오탐을 막습니다. ⑤ 위치는 CSS 선택자로 적되 생성 후 재조회해 단일 요소를 가리키는지
검증합니다.<br><br>
<b>상용 AI API 는 사용하지 않습니다.</b> 이 문제는 규칙으로 완전히 풀리고, 규칙 엔진이 더
빠르고 결과가 매번 같으며 판정 이유를 설명할 수 있기 때문입니다. 따라서 API KEY·.env·외부
서버·GPU 에 해당하는 사항이 없습니다."""


def sign_img():
    return (f'<img class="sig" src="file://{SIGN}">' if SIGN and Path(SIGN).exists()
            else '<span style="display:inline-block;width:26mm"></span>')


def page1():
    return f"""
<div class="form">서식1</div>
<h1>참가 신청서</h1>
<table>
<tr><th style="width:24mm">접수 번호</th><td colspan="3" class="na">※ 접수처에서 기재</td></tr>
<tr><th>지원 형태</th><td colspan="3">■ 개인 &nbsp;&nbsp; □ 팀</td></tr>
<tr><th>대표자 이름</th><td class="v" style="width:52mm">{NAME}</td>
    <th style="width:28mm">대표자 연락처</th><td class="v">{PHONE}</td></tr>
<tr><th>E-Mail</th><td class="v" colspan="3">{EMAIL}</td></tr>
<tr><th>소속</th><td colspan="3">■ 개인 &nbsp; □ 민간기업 &nbsp; □ 대학생 &nbsp; □ 공공기관
    &nbsp; □ 기타<br><span class="na small">기관명 : 해당 없음 &nbsp;&nbsp; 부서 : 해당 없음</span></td></tr>
<tr><th>연령대</th><td colspan="3">■ 20대 미만 &nbsp; □ 20대 &nbsp; □ 30대 &nbsp; □ 40대
    &nbsp; □ 50대 &nbsp; □ 60대 이상</td></tr>
</table>
<table>
<tr><th style="width:24mm">공동참가자</th><th style="width:34mm">이름</th>
    <th style="width:40mm">휴대폰 번호</th><th>이메일</th></tr>
<tr><th>팀원1~4</th><td colspan="3" class="na">해당 없음 (개인 참가)</td></tr>
</table>
<table>
<tr><th style="width:24mm">작품명</th><td class="v"><b>{TITLE}</b></td></tr>
</table>
<table>
<tr><th style="width:24mm">요약(초록)</th><td class="small">{ABSTRACT}</td></tr>
</table>
<table>
<tr><th style="width:24mm">활용 데이터 및<br>주요 기술</th><td class="small">{TECH}</td></tr>
</table>
<p style="margin-top:5mm">&nbsp;&nbsp;위와 같이 『공공 웹사이트 불법광고 탐지 도구 개발
공모전』에 참가를 신청합니다.</p>
<div class="signblk">{DATE}<br>
<span class="signrow">신청인(대표자) &nbsp; {NAME} {sign_img()} (서명)</span>
<div class="to">한국지능정보사회진흥원장 귀하</div></div>
<div class="att"><b>첨부</b>
1. 참가 서약서 1부.<br>2. 개인정보 수집·이용 동의서 1부.<br>3. 기획서 1부.</div>
"""


def page2():
    return f"""
<div class="form">서식2</div>
<h1>참가 서약서</h1>
<div class="sub">『공공 웹사이트 불법광고 탐지 도구 개발 공모전』</div>
<table>
<tr><th style="width:28mm">작품명</th><td class="v" colspan="3"><b>{TITLE}</b></td></tr>
<tr><th rowspan="5">인적 사항<br>(대표자)</th>
    <th style="width:26mm">성명</th><td class="v" colspan="2">{NAME}</td></tr>
<tr><th>전화번호</th><td class="v" colspan="2">{PHONE}</td></tr>
<tr><th>E-mail</th><td class="v" colspan="2">{EMAIL}</td></tr>
<tr><th>주소</th><td class="v" colspan="2">{ADDR}</td></tr>
<tr><th>소속</th><td colspan="2">■ 개인 &nbsp; □ 민간기업 &nbsp; □ 대학생 &nbsp; □ 공공기관
    &nbsp; □ 기타<br><span class="na small">기관명 : 해당 없음 &nbsp;&nbsp; 부서 : 해당 없음</span></td></tr>
</table>
<p class="agree">&nbsp;&nbsp;상기 본인은 『공공 웹사이트 불법광고 탐지 도구 개발 공모전』에
출품함에 있어, 다음 각 호의 규정을 준수할 것을 서약합니다.</p>
<ol class="sv">
<li>대회의 제반 규정을 준수하며, 이를 준수하지 않을 경우, 어떠한 조치도 감수한다.</li>
<li>출품작에 대한 저작권으로 인하여 발생하는 민·형사상 책임은 출품자에게 있다.</li>
<li>타 경진 대회 수상작, 대리 작품 및 타인의 저작물을 표절, 도용, 중복 응모한 경우
    부정행위로 간주하여 심사에서 제외하며, 수상 이후에 그 사실이 밝혀질 경우 수상 취소 및
    상금 등 환수 조치에 동의한다.</li>
<li>공모전의 취지, 목적을 달성하기 위하여 공공 분야에 활용하는 것에 대해 동의한다.
    (수상작에 한함)</li>
</ol>
<p class="agree">&nbsp;&nbsp;서약서 및 신청서 내용이 사실임을 확인하며, 허위 사실 기재 등으로
인하여 어떠한 문제가 발생했을 시, 모든 책임은 본인에게 있음을 확인합니다.</p>
<div class="signblk">{DATE}<br>
<span class="signrow">신청인(대표자) &nbsp; {NAME} {sign_img()} (서명)</span>
<div class="to">한국지능정보사회진흥원장 귀하</div></div>
"""


def page3():
    return f"""
<div class="form">서식3</div>
<h1>개인정보 수집·이용 동의서</h1>
<div class="sub">『공공 웹사이트 불법광고 탐지 도구 개발 공모전』</div>
<div class="box small">
<b>【개인정보 수집·이용 동의 안내】</b><br><br>
<b>가. 개인정보 수집·이용 목적</b><br>
◦ 「공공 웹사이트 불법광고 탐지 도구 개발 공모전」에서 수집되는 개인정보는 정보 주체의
동의를 얻어 '수상작 선정 평가 및 공모전 운영·관리를 목적'으로 이용됩니다.<br><br>
<b>나. 개인정보 수집 항목</b><br>
◦ 신청자명, 연락처, 이메일, 주소<br><br>
<b>다. 개인정보의 보유·이용 기간</b><br>
◦ 수집된 개인정보는 공모전 결과 발표일(또는 사업 종료일)로부터 1년 이내에 지체 없이
파기합니다. 단, 수상자의 개인정보는 상금 지급에 따른 원천징수 및 세무 신고 등 관련
법령(국세기본법 등)에 의거하여 5년간 보존 후 파기합니다.<br><br>
<b>라. 개인정보 수집·이용에 동의하지 않을 권리 및 동의하지 않을 경우의 불이익</b><br>
◦ 정보주체는 「공공 웹사이트 불법광고 탐지 도구 개발 공모전」에 개인정보 수집·이용의
동의를 거부할 권리가 있습니다.<br>
◦ 개인정보 수집·이용에 동의하지 않을 경우, 본 공모전에 참가 신청이 불가합니다.
</div>
<p class="agree">&nbsp;&nbsp;본인은 『공공 웹사이트 불법광고 탐지 도구 개발 공모전』에서
본인의 개인정보를 수집·이용하는 것에 동의합니다.</p>
<p style="text-align:center;font-size:11.5pt;margin-top:2mm">
(동의함 <b>■</b> &nbsp;&nbsp; 동의하지 않음 □)</p>
<div class="signblk">{DATE}<br>
<span class="na" style="font-size:10pt">(※ 해당 시, 팀명 : 해당 없음 — 개인 참가)</span><br>
<span class="signrow">신청인 &nbsp; {NAME} {sign_img()} (서명)</span></div>
"""


def build(name, body):
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
    build("1_참가신청서", page1())
    build("2_참가서약서", page2())
    build("3_개인정보동의서", page3())


if __name__ == "__main__":
    main()
