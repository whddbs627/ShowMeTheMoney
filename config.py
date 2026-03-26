import os
from dotenv import load_dotenv

load_dotenv()

# Upbit API Keys
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY")

if not UPBIT_ACCESS_KEY or not UPBIT_SECRET_KEY:
    raise ValueError("UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY must be set in .env")

# Trading Parameters - Multi Coin
DEFAULT_TICKERS = [
    "KRW-BTC",   # 비트코인
    "KRW-ETH",   # 이더리움
    "KRW-XRP",   # 리플
    "KRW-SOL",   # 솔라나
    "KRW-DOGE",  # 도지코인
    "KRW-ADA",   # 에이다
    "KRW-AVAX",  # 아발란체
    "KRW-DOT",   # 폴카닷
    "KRW-LINK",  # 체인링크
    "KRW-ETC",   # 이더리움클래식
]
TICKERS = os.getenv("TICKERS", ",".join(DEFAULT_TICKERS)).split(",")
TICKERS = [t.strip() for t in TICKERS if t.strip()]

K = float(os.getenv("K", "0.5"))
INVESTMENT_RATIO = float(os.getenv("INVESTMENT_RATIO", "0.5"))
MAX_INVESTMENT_KRW = float(os.getenv("MAX_INVESTMENT_KRW", "100000"))  # per coin
CHECK_INTERVAL_SEC = int(os.getenv("CHECK_INTERVAL_SEC", "10"))

# Filters
USE_MA_FILTER = os.getenv("USE_MA_FILTER", "true").lower() == "true"
USE_RSI_FILTER = os.getenv("USE_RSI_FILTER", "true").lower() == "true"
RSI_LOWER_BOUND = float(os.getenv("RSI_LOWER_BOUND", "30"))

# Risk Management
MAX_LOSS_PCT = float(os.getenv("MAX_LOSS_PCT", "0.03"))

# Notifications
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
