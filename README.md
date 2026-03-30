# ShowMeTheMoney

Upbit 기반 암호화폐 자동매매 플랫폼 — 변동성 돌파 전략 + 실시간 웹 대시보드

## Features

### Trading Bot
- **4가지 매매 전략** — 변동성 돌파, RSI 반등, 골든크로스, 복합 전략
- **프리셋** — 안정형 / 균형형 / 공격형 원클릭 적용
- **자동 익절/손절** — 설정 비율 도달 시 자동 매도
- **일봉 기준 매매** — 09:00 KST 리셋, 당일 1회 매수, 익일 자동 매도
- **봇 자동 복원** — 서버 재시작 시 이전 실행 중이던 봇 자동 재시작

### Dashboard
- **내 코인** — 현재가, 매수목표, 손절가, 익절가, RSI, 추세 실시간 표시
- **차트** — 1시간 ~ 90일 기간 선택 가능한 가격 차트 (인트라데이 지원)
- **수동 매매** — 시장가/지정가 매수·매도 지원
- **미체결 주문** — 대기 중인 주문 확인 및 취소
- **시장 랭킹** — 급등 / 거래대금 / 고가 코인 정렬
- **거래 내역** — 매수·매도 기록 및 누적 손익 차트

### Demo Mode
- API 키 없이 가상 자금으로 매매 연습
- 최대 100억원까지 설정 가능
- 실제 시세 기반, 실제 자산 미노출

### Multi-User
- 회원가입/로그인 (JWT 인증, PBKDF2 해싱)
- 유저별 독립된 봇, 전략, 워치리스트
- 수익률 순위 리더보드
- Discord 웹훅 알림 (매수/매도/에러/시작·중지 개별 설정)

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI, Python 3.12, SQLite (aiosqlite) |
| Frontend | React, TypeScript, Vite, Recharts |
| Infrastructure | Docker Compose, Nginx, AWS EC2 |
| CI/CD | GitHub Actions (Test → Deploy) |
| Exchange | Upbit (pyupbit) |
| Security | JWT, Fernet encryption, Rate limiting |

## Project Structure

```
ShowMeTheMoney/
├── backend/
│   ├── app.py              # FastAPI application & lifespan
│   ├── auth.py             # JWT authentication & encryption
│   ├── database.py         # SQLite schema & CRUD operations
│   ├── engine.py           # Multi-user bot engine
│   ├── security.py         # Rate limiting & error handling
│   ├── upbit_cache.py      # API response cache layer
│   ├── coin_names.py       # Coin metadata (KR/EN names)
│   ├── models.py           # Pydantic request/response models
│   └── routes/             # API route handlers
├── frontend/
│   ├── src/
│   │   ├── App.tsx         # Main layout
│   │   ├── api.ts          # Axios API client
│   │   └── components/     # React components
│   └── Dockerfile          # Multi-stage build → Nginx
├── tests/                  # pytest test suite (44 tests)
├── deploy/                 # AWS deployment scripts
├── config.py               # Environment config loader
├── trader.py               # Core trading logic
├── strategy.py             # Trading strategies (4 types)
├── upbit_api.py            # Upbit exchange API wrapper
├── notifier.py             # Discord webhook notifier
├── docker-compose.yml
└── .github/workflows/      # CI/CD pipeline
```

## Getting Started

### Prerequisites

- Docker & Docker Compose
- Python 3.12+ (for local development)

### Local Development (Docker)

```bash
cp .env.example .env
# Edit .env with your API keys

docker compose up --build -d
# Open http://localhost:3000
```

### AWS Deployment

```bash
./deploy/setup-aws.sh       # Provision EC2 infrastructure
./deploy/deploy.sh <EC2_IP>  # Deploy application
```

### Running Tests

```bash
pip install -r requirements.txt
pip install pytest pytest-asyncio httpx
python -m pytest tests/ -v
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `UPBIT_ACCESS_KEY` | Upbit API Access Key | No (multi-user mode uses per-user keys) |
| `UPBIT_SECRET_KEY` | Upbit API Secret Key | No (multi-user mode uses per-user keys) |
| `JWT_SECRET` | JWT signing key | Yes (production) |
| `ENCRYPT_KEY` | Fernet key for API key encryption | Yes (production) |
| `DISCORD_WEBHOOK_URL` | Discord webhook URL | No |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | No (default: `*`) |

## CI/CD Pipeline

```
push to main
  ├─ Test (Python 3.12, ubuntu-latest)
  │   └─ pytest: strategy, auth, cache, API (44 tests)
  │
  └─ Deploy (on test pass, main branch only)
      ├─ SCP → EC2
      ├─ docker compose rebuild
      └─ Health check (/api/version)
```

## Trading Strategies

### Volatility Breakout (Larry Williams)
```
Buy:  current_price > today_open + (yesterday_high - yesterday_low) × K
Sell: take-profit / next day 09:00 KST / stop-loss
```

### RSI Bounce
```
Buy: RSI crosses above oversold threshold (default: 30)
```

### Golden Cross
```
Buy: 5-day MA crosses above 20-day MA
```

### Combined
```
Buy: volatility breakout + bullish MA trend + RSI in healthy range (30-70)
```

## License

MIT
