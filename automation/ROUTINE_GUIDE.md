# 모닝벨 요약 루틴 가이드

클라우드 루틴(Claude Code)이 매일 아침 이 파일을 읽고 그대로 따른다. 컨텍스트 없이 시작하므로 여기 적힌 것만 믿는다.
같은 저장소의 `README.md` 에 프로젝트 배경과 원장 규칙이 있다 — 읽어두되, 이 루틴은 **요약·전송·커밋**까지만 한다.
종목 선별·원장 기록은 사용자가 따로 한다. 루틴은 추천이나 판단을 하지 않는다.

## 0. 준비

```bash
cd /home/user/sbs_biz            # GitHub 저장소명은 sbs_biz (밑줄). 클론 경로가 다르면 그 경로
git pull --ff-only
python3 -m pip install -q -r requirements.txt
```

오늘 날짜는 **KST** 기준이다 (`TZ=Asia/Seoul date +%F`). 루틴은 UTC 로 돈다는 것을 잊지 말 것.
토·일에는 방송이 없다. `summaries/YYYYMMDD.md` 가 이미 있으면 오늘치는 끝난 것이니 그대로 종료한다.

텔레그램 비밀값은 환경변수 `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` 로 들어온다 (`tg.py` 가 읽는다).
둘 중 하나라도 비어 있으면 요약·커밋까지만 하고 전송은 건너뛰되, 마지막 보고에 그 사실을 적는다.

## 1. 자막 수집

```bash
PYTHONUTF8=1 python3 fetch.py            # data/transcripts/YYYYMMDD.txt 생성
```

- 정상: `2026년 9월 22일 (화) 모닝벨 다시보기 -> data/transcripts/20260922.txt (120,052 bytes)` 같은 한 줄.
- `다시보기가 아직 채널에 없다` → 보통 KST 11시 전에 올라온다. **10분 간격으로 최대 6번** 다시 시도한다
  (`sleep 600`). 그래도 없으면 `summaries/YYYYMMDD_SKIP.md` 에 "다시보기 미업로드, HH:MM KST 기준" 한 줄을 남기고
  4단계(커밋)로 간다. 전송은 하지 않는다.
- yt-dlp 가 YouTube 봇 확인("Sign in to confirm you're not a bot") 등으로 막히면 `summaries/YYYYMMDD_SKIP.md` 에
  오류 메시지 앞 300자를 적고 커밋한다. **다른 우회 방법을 시도하지 않는다** — 사용자가 판단할 문제다.
- 자막이 30,000 바이트 미만이면 뭔가 잘못된 것이다(정상은 100KB 안팎). SKIP 처리하고 크기를 적는다.

## 2. 요약 작성

`data/transcripts/YYYYMMDD.txt` 를 **전부** 읽는다 (Read 로 나눠 읽어도 된다. 앞부분만 읽고 쓰지 말 것).
그다음 `SUMMARY_FORMAT.md` 의 지시를 그대로 따라 요약을 쓴다. 그 파일이 편집자 지시문이자 출력 형식이다.
날짜 자리는 `2026-09-22 (화)` 처럼 채운다.

요약을 `summaries/YYYYMMDD.md` 에 저장한다. 파일 끝에 빈 줄 하나와 `원본: https://www.youtube.com/watch?v=...`
(video_id 는 `data/transcripts/YYYYMMDD.json` 에 있다) 를 붙인다.

자기 점검 세 가지: (1) 방송에 없는 내용이 들어가지 않았는가 (2) "관련:" 뒤 종목은 방송에서 실제 언급됐는가
(3) 출연자 의견이 이슈 항목에 사실처럼 섞이지 않았는가.

## 3. 전송

```bash
python3 tg.py send-file summaries/YYYYMMDD.md
```

`sent` 가 찍히면 성공. 실패하면 오류를 보고에 적되 커밋은 계속한다.

## 4. 커밋·푸시

```bash
git add summaries/
git commit -m "summary: YYYYMMDD 모닝벨"      # SKIP 이면 "summary: YYYYMMDD SKIP (사유)"
git push origin main
```

`data/` 는 gitignore 라 자막은 커밋되지 않는다 (의도된 것). main 푸시가 거부되면 `claude/summaries` 브랜치로 푸시하고 보고에 적는다.

## 5. 마지막 보고 (한 문단)

날짜, 자막 크기, 전송 성공 여부, 커밋 해시. 요약 본문은 다시 붙이지 않는다.
