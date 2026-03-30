import os
from dotenv import load_dotenv

load_dotenv()

# Upbit API Keys (standalone bot용, 웹 대시보드는 유저별 키 사용)
UPBIT_ACCESS_KEY = os.getenv("UPBIT_ACCESS_KEY", "")
UPBIT_SECRET_KEY = os.getenv("UPBIT_SECRET_KEY", "")

# Defaults
TICKER = os.getenv("TICKER", "KRW-BTC")
K = float(os.getenv("K", "0.5"))
INVESTMENT_RATIO = float(os.getenv("INVESTMENT_RATIO", "0.5"))
MAX_INVESTMENT_KRW = float(os.getenv("MAX_INVESTMENT_KRW", "100000"))
CHECK_INTERVAL_SEC = int(os.getenv("CHECK_INTERVAL_SEC", "10"))
USE_MA_FILTER = os.getenv("USE_MA_FILTER", "true").lower() == "true"
USE_RSI_FILTER = os.getenv("USE_RSI_FILTER", "true").lower() == "true"
RSI_LOWER_BOUND = float(os.getenv("RSI_LOWER_BOUND", "30"))
MAX_LOSS_PCT = float(os.getenv("MAX_LOSS_PCT", "0.03"))
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
