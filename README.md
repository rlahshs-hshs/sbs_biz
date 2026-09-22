# sbs-biz

SBS Biz 아침 방송 **모닝벨**(07:00~09:00)을 매일 요약해 텔레그램으로 받고,
거기서 내가 고른 종목 아이디어를 원장에 적어 사후검증한다.

## 흐름

```
유튜브 SBS Biz 채널 (매일 오전 "N월 N일 모닝벨 다시보기" 업로드, 한국어 자동자막)
  → fetch.py      자막 → data/transcripts/YYYYMMDD.txt  (약 120KB, gitignore)
  → summarize.py  Claude API 요약 → summaries/YYYYMMDD.md (git 추적)
  → tg.py         텔레그램 전송
  → 내가 읽고 픽이 있으면 Claude 에게 말해 ledger/picks.jsonl 에 기록
  → 사후검증은 stock-pipeline 의 history.db (get_price_path / get_verify_snapshot) 로
```

## 실행 경로 두 가지

**클라우드 루틴 (기본).** Claude Code 루틴이 평일 아침 `automation/ROUTINE_GUIDE.md` 를 읽고 그대로 한다 —
저장소의 자막 읽기 → 루틴(Claude)이 직접 `SUMMARY_FORMAT.md` 대로 요약 → 텔레그램 전송 → `summaries/` 커밋·푸시.
API 키가 필요 없다(루틴이 곧 Claude). 텔레그램 비밀값은 클라우드 환경의 환경변수
`TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 로 준다.

단, **클라우드 IP 는 유튜브 봇 확인에 걸려 자막을 못 받는다** (2026-09-22 확인 — Anthropic 클라우드 환경도,
네이버클라우드 VM 도 막힘. deno·player_client 변경으로도 안 됨. 가정 회선만 된다). 그래서 자막은 **노트북**에서
`push_transcript.py` 가 받아 `data/transcripts/` 에 커밋·푸시하고, 루틴은 그걸 읽는다.

노트북 쪽은 Windows 작업 스케줄러 `sbs-biz 자막 업로드` (평일 10:05 부터 30분 간격 2시간, 놓치면 켜질 때 실행,
`pythonw.exe -X utf8 push_transcript.py`, 로그 `logs/push_transcript.log`). 루틴 시각(10:30 KST) 전에 올라와
있어야 하며, 없으면 루틴이 10분 간격 6회 기다린 뒤 SKIP 한다. `deploy/vm_setup.sh` 는 VM 이 막히기 전에 만든 것으로,
VM IP 가 풀리면 쓸 수 있다.

**로컬 (예비).** `run.py` 가 수집·요약·전송을 묶는다. 요약은 `summarize.py` 가 Claude API 로 하므로
`anthropic_api_key` 가 필요하다. 실행 환경은 자체 `.venv` (Python 3.11).

```
.venv\Scripts\python.exe run.py            # 오늘치 수집·요약·전송
.venv\Scripts\python.exe run.py --no-send  # 전송 없이 요약만
.venv\Scripts\python.exe tg.py chat-id     # 봇 설정 때 chat_id 확인
```

로컬 비밀값은 `secrets.json` (gitignore): `telegram_bot_token`, `telegram_chat_id`, `anthropic_api_key`.
두 경로 모두 요약 지시문은 `SUMMARY_FORMAT.md` 하나를 쓴다.

요약 끝에는 "주목할 만한 것 (Claude 의견)" 섹션이 붙는다 — 기준은 국내 상장 종목·업종으로 이어지는가 하나.
매수·매도·가격은 안 쓴다. `summaries/` 가 git 에 남으므로 이 의견도 날짜와 함께 기록되는 셈이다.

## 원장 규칙 (ledger/picks.jsonl)

선별은 전적으로 내 감이다. 감에는 규칙을 두지 않는다. 대신 **기록**에는 규칙을 둔다 —
나중에 답이 하나로 나오게 하기 위해서다.

1. **종목 단위로 적는다.** 테마는 태그로만 남긴다. (테마로 적으면 검증 때 대표 종목 선택이 또 판단이 된다)
2. **매수 조건을 적는다.** 지정가(예: 4,500원 오면) 또는 "당일 종가". 지정가는 **유효기간 기본 20거래일**,
   그 안에 안 오면 `미체결`로 따로 센다. 픽마다 기한을 달리 적을 수 있다.
3. **삭제하지 않는다.** 결과가 나빠도 남긴다. 지우기 시작하면 기억에 남은 성공 사례만 남는 것과 같아진다.
4. **정정은 새 줄로.** 조건을 바꾸면 원래 줄은 두고 `supersedes` 로 잇는다.

한 줄 형식:

```json
{"id": "P-0001", "logged": "2026-09-22", "ticker": "329180", "name": "HD현대중공업",
 "entry": {"type": "limit", "price": 4500, "valid_days": 20},
 "themes": ["조선"], "source": "모닝벨 2026-09-22", "note": "한 줄 이유"}
```

`entry.type` 은 `limit`(지정가) 또는 `close`(기록일 종가). 검증 결과는 이 파일에 쓰지 않고 별도 산출한다.

## 미디어 언급 효과는 재지 않는다

방송이 언급한 것 전부를 적어 "언급 → 수익" 을 재는 설계도 가능하지만, 사용자 결정으로 하지 않는다.
이 원장이 재는 것은 **방송을 보고 내가 고른 것**의 성적뿐이다. 결론도 그 범위 안에서만 쓴다.
