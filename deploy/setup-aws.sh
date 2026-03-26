#!/bin/bash
set -e

# ============================================
# ShowMeTheMoney - AWS EC2 배포 스크립트
# ============================================
# 사용법: ./deploy/setup-aws.sh
#
# 사전 조건:
#   1. AWS CLI 설치 + 설정 (aws configure)
#   2. 리전 설정 (기본: ap-northeast-2 서울)
# ============================================

REGION="ap-northeast-2"
INSTANCE_TYPE="t3.micro"
KEY_NAME="showmethemoney-key"
SG_NAME="showmethemoney-sg"
PROJECT_NAME="ShowMeTheMoney"

echo "=== $PROJECT_NAME AWS 배포 시작 ==="

# 1. 키 페어 생성
echo "[1/5] SSH 키 페어 생성..."
if aws ec2 describe-key-pairs --key-names "$KEY_NAME" --region "$REGION" &>/dev/null; then
    echo "  키 페어 '$KEY_NAME' 이미 존재. 스킵."
else
    aws ec2 create-key-pair \
        --key-name "$KEY_NAME" \
        --query 'KeyMaterial' \
        --output text \
        --region "$REGION" > "${KEY_NAME}.pem"
    chmod 400 "${KEY_NAME}.pem"
    echo "  키 페어 생성 완료: ${KEY_NAME}.pem"
fi

# 2. 보안 그룹 생성
echo "[2/5] 보안 그룹 생성..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text --region "$REGION")

SG_ID=$(aws ec2 describe-security-groups --filters "Name=group-name,Values=$SG_NAME" --query "SecurityGroups[0].GroupId" --output text --region "$REGION" 2>/dev/null || echo "None")

if [ "$SG_ID" = "None" ] || [ -z "$SG_ID" ]; then
    SG_ID=$(aws ec2 create-security-group \
        --group-name "$SG_NAME" \
        --description "ShowMeTheMoney trading bot" \
        --vpc-id "$VPC_ID" \
        --query "GroupId" \
        --output text \
        --region "$REGION")

    # SSH (22)
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 22 --cidr 0.0.0.0/0 --region "$REGION"
    # Web (3000)
    aws ec2 authorize-security-group-ingress --group-id "$SG_ID" --protocol tcp --port 3000 --cidr 0.0.0.0/0 --region "$REGION"

    echo "  보안 그룹 생성 완료: $SG_ID (22, 3000 포트 오픈)"
else
    echo "  보안 그룹 '$SG_NAME' 이미 존재: $SG_ID"
fi

# 3. 최신 Amazon Linux 2023 AMI 찾기
echo "[3/5] AMI 조회..."
AMI_ID=$(aws ec2 describe-images \
    --owners amazon \
    --filters "Name=name,Values=al2023-ami-2023*-x86_64" "Name=state,Values=available" \
    --query "sort_by(Images, &CreationDate)[-1].ImageId" \
    --output text \
    --region "$REGION")
echo "  AMI: $AMI_ID"

# 4. EC2 인스턴스 생성
echo "[4/5] EC2 인스턴스 생성 ($INSTANCE_TYPE)..."
INSTANCE_ID=$(aws ec2 run-instances \
    --image-id "$AMI_ID" \
    --instance-type "$INSTANCE_TYPE" \
    --key-name "$KEY_NAME" \
    --security-group-ids "$SG_ID" \
    --user-data file://deploy/user-data.sh \
    --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$PROJECT_NAME}]" \
    --block-device-mappings '[{"DeviceName":"/dev/xvda","Ebs":{"VolumeSize":20,"VolumeType":"gp3"}}]' \
    --query "Instances[0].InstanceId" \
    --output text \
    --region "$REGION")
echo "  인스턴스 생성: $INSTANCE_ID"

# 인스턴스 실행 대기
echo "  인스턴스 시작 대기 중..."
aws ec2 wait instance-running --instance-ids "$INSTANCE_ID" --region "$REGION"

# 5. Elastic IP 할당
echo "[5/5] Elastic IP 할당..."
ALLOC_ID=$(aws ec2 allocate-address --domain vpc --query "AllocationId" --output text --region "$REGION")
EIP=$(aws ec2 describe-addresses --allocation-ids "$ALLOC_ID" --query "Addresses[0].PublicIp" --output text --region "$REGION")
aws ec2 associate-address --instance-id "$INSTANCE_ID" --allocation-id "$ALLOC_ID" --region "$REGION"

echo ""
echo "============================================"
echo "  배포 완료!"
echo "============================================"
echo "  Instance ID : $INSTANCE_ID"
echo "  Public IP   : $EIP"
echo "  SSH 접속    : ssh -i ${KEY_NAME}.pem ec2-user@${EIP}"
echo "  대시보드    : http://${EIP}:3000"
echo ""
echo "  다음 단계:"
echo "  1. 잠시 대기 (인스턴스 초기화 ~2분)"
echo "  2. ./deploy/deploy.sh $EIP 실행"
echo "============================================"
