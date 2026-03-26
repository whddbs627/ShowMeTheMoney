# ShowMeTheMoney

코인 자동매매 플랫폼 - 업비트 기반 변동성 돌파 전략 + 웹 대시보드

## 주요 기능

### 자동매매 봇
- **4가지 매매 전략**: 변동성 돌파, RSI 반등, 골든크로스, 복합 전략
- **프리셋**: 안정형 / 균형형 / 공격형 원클릭 적용
- **자동 익절/손절**: 설정 비율 도달 시 자동 매도
- **일봉 기준 매매**: 09:00 KST 리셋, 당일 1회 매수, 익일 자동 매도

### 대시보드
- **내 코인**: 현재가, 매수목표, 손절가, 익절가, RSI, 추세 실시간 표시
- **차트**: 1시간 ~ 90일 기간 선택 가능한 가격 차트
- **수동 매매**: 시장가/지정가 매수, 지정가 매도 지원
- **미체결 주문**: 대기 중인 주문 확인 및 취소
- **시장 랭킹**: 급등 / 거래대금 / 고가 코인 정렬

### 가상계좌 (데모 모드)
- API 키 없이 가상 자금으로 매매 연습
- 최대 100억원까지 설정 가능
- 실제 시세 기반, 실제 자산 미노출

### 멀티유저
- 회원가입/로그인 (JWT 인증)
- 유저별 독립된 봇, 전략, 워치리스트
- 수익률 순위 리더보드
- 디스코드 웹훅 알림 (매수/매도/에러/시작중지 개별 설정)

## 기술 스택

| 영역 | 기술 |
|---|---|
| Backend | FastAPI, Python 3.12, SQLite (aiosqlite) |
| Frontend | React, TypeScript, Vite, Recharts |
| Infra | Docker Compose, nginx, AWS EC2 |
| CI/CD | GitHub Actions (테스트 → 배포) |
| 거래소 | Upbit (pyupbit) |

## 프로젝트 구조

```
ShowMeTheMoney/
├── backend/
│   ├── app.py              # FastAPI 앱
│   ├── auth.py             # JWT 인증, 암호화
│   ├── database.py         # SQLite 스키마 + CRUD
│   ├── engine.py           # 자동매매 봇 엔진 (멀티유저)
│   ├── security.py         # Rate limiting, 에러 핸들링
│   ├── upbit_cache.py      # Upbit API 캐시 레이어
│   └── routes/             # API 라우트
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # 메인 레이아웃
│   │   ├── api.ts          # API 클라이언트
│   │   └── components/     # React 컴포넌트
│   └── Dockerfile          # nginx 빌드
├── tests/                  # 테스트 코드
├── deploy/                 # AWS 배포 스크립트
├── docker-compose.yml
└── .github/workflows/      # CI/CD 파이프라인
```

## 설치 및 실행

### 로컬 (Docker)

```bash
# .env 설정
cp .env.example .env
vi .env  # API 키, JWT_SECRET, ENCRYPT_KEY 입력

# 실행
docker compose up --build -d

# 접속: http://localhost:3000
```

### AWS 배포

```bash
# 1. 인프라 생성
./deploy/setup-aws.sh

# 2. 코드 배포
./deploy/deploy.sh <EC2_IP>
```

### 테스트

```bash
pip install -r requirements.txt pytest pytest-asyncio httpx
python -m pytest tests/ -v
```

## 환경변수 (.env)

| 변수 | 설명 | 필수 |
|---|---|---|
| `UPBIT_ACCESS_KEY` | 업비트 Access Key | O |
| `UPBIT_SECRET_KEY` | 업비트 Secret Key | O |
| `JWT_SECRET` | JWT 서명 키 | O (프로덕션) |
| `ENCRYPT_KEY` | API 키 암호화 키 (Fernet) | O (프로덕션) |
| `DISCORD_WEBHOOK_URL` | 디스코드 웹훅 URL | X |
| `CORS_ORIGINS` | CORS 허용 도메인 | X (기본: *) |

## CI/CD 파이프라인

```
push to main
  ├── Test (Python 3.12)
  │   ├── 전략 로직 테스트
  │   ├── 인증/암호화 테스트
  │   ├── 캐시 레이어 테스트
  │   └── API 통합 테스트
  │
  └── Deploy (테스트 통과 시)
      ├── SCP → EC2
      ├── docker-compose rebuild
      └── Health check
```

## 매매 전략

### 변동성 돌파 (Larry Williams)
```
매수: 현재가 > 당일시가 + (전일고가 - 전일저가) × K
매도: 익절가 도달 / 익일 09:00 / 손절가 도달
```

### RSI 반등
```
매수: RSI가 과매도 구간(하한) 아래에서 위로 돌파
```

### 골든크로스
```
매수: 5일 이동평균이 20일 이동평균을 상향 돌파
```

### 복합 전략
```
매수: 변동성 돌파 + 상승추세(MA) + RSI 양호 모두 충족
```

## 라이선스

MIT
