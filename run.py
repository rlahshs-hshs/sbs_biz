"""하루치 파이프라인: 자막 수집 → 요약 → 텔레그램 전송.

    .venv\\Scripts\\python.exe run.py               # 오늘
    .venv\\Scripts\\python.exe run.py 2026-09-22    # 특정 날짜
    .venv\\Scripts\\python.exe run.py --no-send     # 요약만 만들고 보내지 않음

요약은 summaries/YYYYMMDD.md 에 남는다. 이미 있으면 다시 요약하지 않고 그대로 보낸다.
다시보기가 아직 안 올라왔으면(주말·휴일 포함) 종료코드 2 로 조용히 끝난다 — 스케줄러가 재시도하게.
"""
import datetime as dt
import sys
from pathlib import Path

from fetch import get_transcript
from summarize import summarize
import tg

ROOT = Path(__file__).resolve().parent
SUMMARIES = ROOT / "summaries"


def main(argv: list[str]) -> int:
    send = "--no-send" not in argv
    days = [a for a in argv if not a.startswith("--")]
    day = dt.date.fromisoformat(days[0]) if days else dt.date.today()

    try:
        txt, info = get_transcript(day)
    except FileNotFoundError as e:
        print(e)
        return 2

    SUMMARIES.mkdir(exist_ok=True)
    out = SUMMARIES / f"{day:%Y%m%d}.md"
    if out.exists():
        summary = out.read_text(encoding="utf-8")
        print(f"기존 요약 사용: {out}")
    else:
        summary = summarize(txt.read_text(encoding="utf-8"), f"{day:%Y-%m-%d}")
        out.write_text(summary + f"\n\n원본: {info['url']}\n", encoding="utf-8")
        print(f"요약 저장: {out}")

    if send:
        tg.send(summary + f"\n\n원본: {info['url']}")
        print("텔레그램 전송 완료")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
