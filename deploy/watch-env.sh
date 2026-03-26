#!/bin/bash
# .env 파일 변경 감지 시 자동 docker-compose rebuild
# systemd 서비스로 실행됨

APP_DIR="/home/ec2-user/app"
ENV_FILE="${APP_DIR}/.env"
HASH_FILE="/tmp/.env.md5"

# 초기 해시 저장
md5sum "$ENV_FILE" > "$HASH_FILE" 2>/dev/null

echo "[watch-env] Watching $ENV_FILE for changes..."

while true; do
    sleep 5

    if [ ! -f "$ENV_FILE" ]; then
        continue
    fi

    NEW_HASH=$(md5sum "$ENV_FILE")
    OLD_HASH=$(cat "$HASH_FILE" 2>/dev/null)

    if [ "$NEW_HASH" != "$OLD_HASH" ]; then
        echo "[watch-env] .env changed, rebuilding..."
        md5sum "$ENV_FILE" > "$HASH_FILE"
        cd "$APP_DIR" && docker-compose up --build -d 2>&1
        echo "[watch-env] Rebuild complete."
    fi
done
