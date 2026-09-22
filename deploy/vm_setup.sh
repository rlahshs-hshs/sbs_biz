#!/usr/bin/env bash
# 네이버클라우드 VM 에 자막 업로더를 설치한다. root 로 한 번 실행.
#   bash <(curl -fsSL https://raw.githubusercontent.com/rlahshs-hshs/sbs_biz/main/deploy/vm_setup.sh)
# 하는 일: 저장소 클론(/root/sbs_biz) → venv + yt-dlp → deno → 배포키 생성(GitHub 에 등록 필요) → cron 등록.
set -euo pipefail

REPO_SSH="git@github.com:rlahshs-hshs/sbs_biz.git"
REPO_HTTPS="https://github.com/rlahshs-hshs/sbs_biz.git"
DIR=/root/sbs_biz
KEY=/root/.ssh/sbs_biz_deploy

# 1. 배포키 — 푸시 권한이 있어야 하므로 GitHub 저장소 Settings → Deploy keys 에 "Allow write access" 로 등록한다.
if [ ! -f "$KEY" ]; then
  ssh-keygen -t ed25519 -N "" -f "$KEY" -C "sbs_biz-vm" >/dev/null
fi
grep -q "Host github.com-sbs_biz" /root/.ssh/config 2>/dev/null || cat >> /root/.ssh/config <<EOF
Host github.com-sbs_biz
  HostName github.com
  User git
  IdentityFile $KEY
  IdentitiesOnly yes
EOF
ssh-keyscan -t ed25519 github.com >> /root/.ssh/known_hosts 2>/dev/null || true

# 2. 저장소 (읽기는 HTTPS 로 되지만 푸시는 배포키 SSH 로 하도록 remote 를 바꾼다)
if [ ! -d "$DIR/.git" ]; then
  git clone -q "$REPO_HTTPS" "$DIR"
fi
cd "$DIR"
git remote set-url origin "${REPO_SSH/github.com/github.com-sbs_biz}"
git config user.name "sbs_biz-vm"
git config user.email "sbs_biz-vm@users.noreply.github.com"

# 3. 파이썬·yt-dlp·deno
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q --upgrade yt-dlp requests
[ -x /root/.deno/bin/deno ] || (curl -fsSL https://deno.land/install.sh | sh >/dev/null 2>&1)

# 4. cron — 평일 10:05 부터 30분 간격으로 12:05 까지. push_transcript.py 는 멱등이라 이미 올렸으면 바로 끝난다.
mkdir -p logs
CRON_LINE="5,35 10-12 * * 1-5 cd $DIR && PYTHONUTF8=1 PATH=/root/.deno/bin:\$PATH .venv/bin/python push_transcript.py >> logs/push_transcript.log 2>&1"
( crontab -l 2>/dev/null | grep -v push_transcript.py; echo "$CRON_LINE" ) | crontab -
# VM 시간대가 UTC 면 KST 10:05 = UTC 01:05 이므로 위 시각을 1,35 1-3 으로 바꿔야 한다. 아래 출력으로 확인.
echo "VM timezone: $(cat /etc/timezone 2>/dev/null || timedatectl show -p Timezone --value 2>/dev/null || date +%Z)"

echo
echo "=== GitHub 저장소 Settings → Deploy keys → Add deploy key (Allow write access 체크) 에 아래 한 줄을 등록 ==="
cat "$KEY.pub"
echo "=== 등록 후 테스트: cd $DIR && PYTHONUTF8=1 PATH=/root/.deno/bin:\$PATH .venv/bin/python push_transcript.py ==="
