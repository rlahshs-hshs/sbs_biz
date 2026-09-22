"""자막을 받아 저장소에 커밋·푸시한다. 유튜브 접근이 되는 곳(노트북·VM)에서 돌리고, 클라우드 루틴은 저장소의 자막을 읽는다.

    python3 push_transcript.py              # 오늘 (KST)
    python3 push_transcript.py 2026-09-22

다시보기가 아직 없으면 종료코드 2 (스케줄러가 다시 부르게). 이미 저장소에 있으면 아무것도 안 하고 0.
"""
import datetime as dt
import subprocess
import sys
from pathlib import Path

from fetch import OUT, get_transcript

ROOT = Path(__file__).resolve().parent
KST = dt.timezone(dt.timedelta(hours=9))  # Windows 파이썬엔 tzdata 가 없어 zoneinfo 를 못 쓴다


def git(*args: str) -> str:
    r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[-500:]}")
    return r.stdout.strip()


def main(argv: list[str]) -> int:
    day = dt.date.fromisoformat(argv[0]) if argv else dt.datetime.now(KST).date()
    if day.weekday() >= 5:
        print(f"{day} 주말 — 방송 없음")
        return 0
    git("pull", "-q", "--ff-only", "origin", "main")
    txt = OUT / f"{day:%Y%m%d}.txt"
    if txt.exists() and git("ls-files", str(txt.relative_to(ROOT))):
        print(f"이미 저장소에 있음: {txt.name}")
        return 0
    try:
        path, info = get_transcript(day)
    except FileNotFoundError as e:
        print(e)
        return 2
    size = path.stat().st_size
    if size < 30_000:
        print(f"자막이 너무 작다 ({size:,} bytes) — 올리지 않음")
        return 3
    rel = str(OUT.relative_to(ROOT)).replace("\\", "/")
    git("add", f"{rel}/{day:%Y%m%d}.txt", f"{rel}/{day:%Y%m%d}.json")
    git("commit", "-q", "-m", f"transcript: {day:%Y%m%d} {info['title']}")
    git("push", "-q", "origin", "main")
    print(f"푸시 완료: {info['title']} ({size:,} bytes)")
    return 0


if __name__ == "__main__":
    if sys.stdout is None:  # pythonw.exe (작업 스케줄러, 창 없음) — 출력을 로그 파일로
        (ROOT / "logs").mkdir(exist_ok=True)
        sys.stdout = sys.stderr = open(ROOT / "logs" / "push_transcript.log", "a", encoding="utf-8")
    print(f"--- {dt.datetime.now(KST):%Y-%m-%d %H:%M} KST")
    try:
        code = main(sys.argv[1:])
    except Exception as e:  # 스케줄러에서는 예외도 로그에 남아야 한다
        print(f"오류: {e}")
        code = 1
    sys.stdout.flush()
    sys.exit(code)
