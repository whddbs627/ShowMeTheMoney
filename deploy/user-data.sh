#!/bin/bash
set -e

# EC2 인스턴스 초기 세팅 스크립트 (Amazon Linux 2023)

# Docker 설치
dnf update -y
dnf install -y docker git
systemctl enable docker
systemctl start docker

# Docker Compose 설치
DOCKER_COMPOSE_VERSION="v2.29.1"
curl -L "https://github.com/docker/compose/releases/download/${DOCKER_COMPOSE_VERSION}/docker-compose-linux-x86_64" \
  -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# ec2-user에 docker 권한
usermod -aG docker ec2-user

# 프로젝트 디렉토리
mkdir -p /home/ec2-user/app
chown ec2-user:ec2-user /home/ec2-user/app

echo "=== Setup complete ==="
