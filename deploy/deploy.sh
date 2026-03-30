#!/bin/bash
set -e

# ============================================
# ShowMeTheMoney - 코드 배포 스크립트
# ============================================
# 사용법: ./deploy/deploy.sh <EC2_IP>
# 코드 변경 후 재배포할 때도 이 스크립트 실행
# ============================================

if [ -z "$1" ]; then
    echo "사용법: $0 <EC2_PUBLIC_IP>"
    exit 1
fi

EC2_IP=$1
KEY_FILE="showmethemoney-key.pem"
REMOTE_DIR="/home/ec2-user/app"
SSH_OPTS="-i $KEY_FILE -o StrictHostKeyChecking=no"

echo "=== 코드 배포: $EC2_IP ==="

# .env 파일 확인
if [ ! -f .env ]; then
    echo "[ERROR] .env 파일이 없습니다. 업비트 API 키를 설정하세요."
    echo "  cp .env.example .env && vi .env"
    exit 1
fi

# 1. 프로젝트 파일 전송
echo "[1/3] 파일 전송 중..."
rsync -avz --exclude '.git' \
    --exclude 'node_modules' \
    --exclude 'venv' \
    --exclude '.venv' \
    --exclude 'frontend/dist' \
    --exclude 'data' \
    --exclude 'logs' \
    --exclude '__pycache__' \
    --exclude '*.pem' \
    --exclude '.env' \
    -e "ssh $SSH_OPTS" \
    ./ ec2-user@${EC2_IP}:${REMOTE_DIR}/

# 2. Docker Compose 빌드 및 실행
echo "[2/3] Docker 컨테이너 빌드 및 실행..."
ssh $SSH_OPTS ec2-user@${EC2_IP} << 'REMOTE_CMD'
    cd /home/ec2-user/app

    # Docker 준비 대기
    for i in {1..30}; do
        if docker info &>/dev/null; then
            break
        fi
        echo "  Docker 시작 대기 중... ($i/30)"
        sleep 2
    done

    docker-compose down 2>/dev/null || true
    docker-compose up --build -d
    docker-compose ps
REMOTE_CMD

# 3. 상태 확인
echo "[3/3] 배포 확인..."
sleep 3
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "http://${EC2_IP}:3000/api/bot/status" || echo "000")

if [ "$HTTP_STATUS" = "200" ]; then
    echo ""
    echo "============================================"
    echo "  배포 성공!"
    echo "============================================"
    echo "  대시보드: http://${EC2_IP}:3000"
    echo "  SSH 접속: ssh -i ${KEY_FILE} ec2-user@${EC2_IP}"
    echo "============================================"
else
    echo ""
    echo "[WARNING] API 응답 없음 (HTTP: $HTTP_STATUS)"
    echo "  컨테이너 시작에 시간이 걸릴 수 있습니다."
    echo "  확인: ssh -i ${KEY_FILE} ec2-user@${EC2_IP} 'cd app && docker-compose logs'"
fi
