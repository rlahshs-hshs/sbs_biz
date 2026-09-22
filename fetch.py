"""SBS Biz 유튜브 채널에서 특정 날짜의 모닝벨 다시보기를 찾아 한국어 자동자막을 평문으로 저장한다.

    .venv\\Scripts\\python.exe fetch.py            # 오늘
    .venv\\Scripts\\python.exe fetch.py 2026-09-22

산출: data/transcripts/YYYYMMDD.txt  (이미 있으면 다시 받지 않는다)
"""
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable
CHANNEL = "https://www.youtube.com/channel/UCbMjg2EvXs_RUGW-KrdM3pw/videos"
OUT = ROOT / "data" / "transcripts"
PROGRAM = "모닝벨"


def _js_runtime_args() -> list[str]:
    """yt-dlp 2026+ 는 YouTube 에 JS 런타임(deno)이 필요하다. PATH 에 없으면 ~/.deno/bin 도 본다."""
    deno = shutil.which("deno") or next((p for p in [Path.home() / ".deno" / "bin" / "deno"] if p.exists()), None)
    return ["--js-runtimes", f"deno:{deno}"] if deno else []


def _ytdlp(*args: str) -> str:
    r = subprocess.run([PY, "-m", "yt_dlp", *_js_runtime_args(), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(f"yt-dlp 실패: {r.stderr[-800:]}")
    return r.stdout


def find_replay(day: dt.date, program: str = PROGRAM, scan: int = 80) -> tuple[str, str] | None:
    """채널 최신 업로드 `scan` 개에서 '2026년 9월 22일 (화) 모닝벨 다시보기' 를 찾는다. (id, title) 또는 None."""
    out = _ytdlp("--flat-playlist", "--playlist-end", str(scan), "--print", "%(id)s\t%(title)s", CHANNEL)
    want = f"{day.year}년 {day.month}월 {day.day}일"
    for line in out.splitlines():
        vid, _, title = line.partition("\t")
        if want in title and program in title and "다시보기" in title:
            return vid, title
    return None


def download_transcript(video_id: str) -> str:
    """ko-orig 자동자막 vtt 를 받아 중복 큐를 제거한 평문으로 돌려준다."""
    tmp = ROOT / "data" / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    _ytdlp("--skip-download", "--write-auto-subs", "--sub-langs", "ko-orig", "--sub-format", "vtt",
           "-o", str(tmp / "%(id)s"), f"https://www.youtube.com/watch?v={video_id}")
    vtt = next(tmp.glob(f"{video_id}*.vtt"))
    text = vtt_to_text(vtt.read_text(encoding="utf-8"))
    vtt.unlink()
    return text


def vtt_to_text(vtt: str) -> str:
    """유튜브 자동자막 vtt 는 같은 줄이 롤링으로 두 번씩 나온다. 태그 제거 + 연속 중복 제거."""
    lines, prev = [], None
    for raw in vtt.splitlines():
        if not raw.strip() or raw.startswith(("WEBVTT", "Kind:", "Language:")) or "-->" in raw:
            continue
        s = re.sub(r"<[^>]+>", "", raw).replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&").strip()
        if s and s != prev:
            lines.append(s)
            prev = s
    return "\n".join(lines)


def get_transcript(day: dt.date) -> tuple[Path, dict]:
    """해당 날짜 자막 파일 경로와 메타(json) 를 돌려준다. 없으면 받아서 만든다."""
    OUT.mkdir(parents=True, exist_ok=True)
    txt = OUT / f"{day:%Y%m%d}.txt"
    meta = OUT / f"{day:%Y%m%d}.json"
    if txt.exists() and meta.exists():
        return txt, json.loads(meta.read_text(encoding="utf-8"))
    found = find_replay(day)
    if not found:
        raise FileNotFoundError(f"{day} {PROGRAM} 다시보기가 아직 채널에 없다")
    vid, title = found
    txt.write_text(download_transcript(vid), encoding="utf-8")
    info = {"date": day.isoformat(), "video_id": vid, "title": title, "url": f"https://www.youtube.com/watch?v={vid}"}
    meta.write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
    return txt, info


if __name__ == "__main__":
    day = dt.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else dt.date.today()
    path, info = get_transcript(day)
    print(info["title"], "->", path, f"({path.stat().st_size:,} bytes)")
