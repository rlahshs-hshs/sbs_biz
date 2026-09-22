"""텔레그램 전송 헬퍼.

비밀값은 환경변수 TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID (클라우드 루틴) 가 있으면 그것,
없으면 secrets.json (로컬, gitignore).

    .venv\\Scripts\\python.exe tg.py chat-id        # 봇에게 아무 말이나 보낸 뒤 실행 → chat_id 출력
    .venv\\Scripts\\python.exe tg.py send "테스트"   # 전송 테스트
    .venv\\Scripts\\python.exe tg.py send-file summaries/20260922.md
"""
import json
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
SECRETS = ROOT / "secrets.json"


def _secrets() -> dict:
    """환경변수(클라우드 루틴) 우선, 없으면 secrets.json(로컬)."""
    def _env(name: str) -> str:  # 리눅스 환경변수는 대소문자를 구분한다 — 소문자로 넣은 경우도 받는다
        return os.environ.get(name.upper()) or os.environ.get(name.lower()) or ""

    env = {"telegram_bot_token": _env("TELEGRAM_BOT_TOKEN"), "telegram_chat_id": _env("TELEGRAM_CHAT_ID")}
    if all(env.values()):
        return env
    if not SECRETS.exists():
        sys.exit(f"환경변수 TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID 도, {SECRETS} 도 없다")
    return {**json.loads(SECRETS.read_text(encoding="utf-8")), **{k: v for k, v in env.items() if v}}


def _api(method: str, **params):
    token = _secrets()["telegram_bot_token"]
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=params, timeout=30)
    data = r.json()
    if not data.get("ok"):
        raise RuntimeError(f"telegram {method}: {data}")
    return data["result"]


def get_chat_id() -> list[tuple[int, str]]:
    """봇이 최근 받은 메시지들의 (chat_id, 보낸 사람) 목록."""
    seen = {}
    for u in _api("getUpdates"):
        msg = u.get("message") or u.get("channel_post") or {}
        chat = msg.get("chat")
        if chat:
            seen[chat["id"]] = chat.get("username") or chat.get("first_name") or chat.get("title") or "?"
    return list(seen.items())


def send(text: str, chat_id: str | None = None) -> None:
    """마크다운 없이 평문 전송. 4096자 넘으면 나눠 보낸다."""
    chat_id = chat_id or _secrets()["telegram_chat_id"]
    limit = 4000
    for i in range(0, len(text), limit):
        _api("sendMessage", chat_id=chat_id, text=text[i:i + limit], disable_web_page_preview=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "chat-id":
        rows = get_chat_id()
        if not rows:
            print("받은 메시지가 없다. 텔레그램에서 봇을 열어 /start 또는 아무 말이나 보낸 뒤 다시 실행.")
        for cid, who in rows:
            print(f"chat_id={cid}  ({who})")
    elif cmd == "send":
        send(" ".join(sys.argv[2:]) or "sbs-biz 테스트")
        print("sent")
    elif cmd == "send-file":
        send(Path(sys.argv[2]).read_text(encoding="utf-8").strip())
        print("sent")
    elif cmd == "check":  # 비밀값 유무만 출력 (값은 절대 출력하지 않는다)
        s = _secrets()
        for k in ("telegram_bot_token", "telegram_chat_id"):
            print(f"{k}: {'있음' if s.get(k) else '없음'}")
        sys.exit(0 if all(s.get(k) for k in ("telegram_bot_token", "telegram_chat_id")) else 1)
    else:
        print(__doc__)
