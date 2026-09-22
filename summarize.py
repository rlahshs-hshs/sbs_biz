"""모닝벨 자막 → 핸드폰용 요약. Claude API 사용.

    .venv\\Scripts\\python.exe summarize.py data/transcripts/20260922.txt

인증: 환경변수 ANTHROPIC_API_KEY, 없으면 secrets.json 의 "anthropic_api_key".
"""
import json
import os
import sys
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent
MODEL = "claude-opus-5"

SYSTEM = (ROOT / "SUMMARY_FORMAT.md").read_text(encoding="utf-8")  # 편집자 지시문·출력 형식 (루틴과 공유)


def _client() -> anthropic.Anthropic:
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        secrets = ROOT / "secrets.json"
        if secrets.exists():
            key = json.loads(secrets.read_text(encoding="utf-8")).get("anthropic_api_key") or None
    return anthropic.Anthropic(api_key=key)  # None 이면 SDK 가 프로필 등 다른 경로를 탐색한다


def summarize(transcript: str, date_label: str) -> str:
    client = _client()
    # 자막이 10만 자 넘게 들어가므로 스트리밍으로 받는다. 안전 분류기 거절 시 서버가 대체 모델로 이어 준다.
    with client.beta.messages.stream(
        model=MODEL,
        max_tokens=8000,
        betas=["server-side-fallback-2026-07-01"],
        fallbacks="default",
        system=SYSTEM,
        messages=[{"role": "user", "content": f"방송 날짜: {date_label}\n\n<자막>\n{transcript}\n</자막>"}],
    ) as stream:
        msg = stream.get_final_message()
    if msg.stop_reason == "refusal":
        raise RuntimeError(f"모델 거절: {msg.stop_details}")
    if msg.stop_reason == "max_tokens":
        raise RuntimeError("출력이 max_tokens 에서 잘렸다")
    text = "".join(b.text for b in msg.content if b.type == "text").strip()
    u = msg.usage
    print(f"[usage] in={u.input_tokens} out={u.output_tokens} model={msg.model}", file=sys.stderr)
    return text


if __name__ == "__main__":
    path = Path(sys.argv[1])
    label = f"{path.stem[:4]}-{path.stem[4:6]}-{path.stem[6:8]}" if path.stem.isdigit() else path.stem
    print(summarize(path.read_text(encoding="utf-8"), label))
