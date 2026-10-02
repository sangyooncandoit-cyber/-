"""윈도우에서 한글을 찍으면 죽는 것을 막는다.

윈도우 콘솔 기본 코드페이지가 cp949/cp1252 라 한글을 한 줄 찍는 순간
UnicodeEncodeError 로 프로그램이 끝난다. 리눅스에서는 재현되지 않는다.
chcp 65001 을 먼저 해도 파이썬 쪽 출력 인코딩은 그대로다.

한글을 출력하는 모든 스크립트가 맨 앞에서 이것을 부른다.
app.py 에만 넣어 뒀다가 보조 스크립트들이 윈도우 빌드에서 그대로 죽었다.
"""
import sys


def force_utf8():
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, OSError):
            pass
