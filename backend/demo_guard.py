"""
데모 모드 악용 방지 모듈
- 서버 소유자 API 키를 데모 유저에게 공유 (읽기 전용)
- 거래 쿨다운, 일일 한도, 계정 수 제한
"""
import os
import time
import logging
from collections import defaultdict
from upbit_api import UpbitAPI

logger = logging.getLogger(__name__)

# 서버 소유자의 데모용 API 키
DEMO_ACCESS_KEY = os.getenv("DEMO_UPBIT_ACCESS_KEY", "")
DEMO_SECRET_KEY = os.getenv("DEMO_UPBIT_SECRET_KEY", "")

# 제한 설정
DEMO_MAX_ACCOUNTS = int(os.getenv("DEMO_MAX_ACCOUNTS", "50"))
DEMO_TRADE_COOLDOWN_SEC = int(os.getenv("DEMO_TRADE_COOLDOWN_SEC", "5"))
DEMO_MAX_BALANCE = float(os.getenv("DEMO_MAX_BALANCE", "1000000000"))  # 10억
DEMO_DAILY_TRADE_LIMIT = int(os.getenv("DEMO_DAILY_TRADE_LIMIT", "100"))

# 유저별 거래 추적
_trade_timestamps: dict[int, list[float]] = defaultdict(list)
_last_trade_time: dict[int, float] = {}


def get_demo_api() -> UpbitAPI | None:
    """데모용 공유 API 인스턴스 반환 (읽기 전용 용도)"""
    if not DEMO_ACCESS_KEY or not DEMO_SECRET_KEY:
        return None
    return UpbitAPI(DEMO_ACCESS_KEY, DEMO_SECRET_KEY)


def has_demo_api() -> bool:
    """서버에 데모용 API 키가 설정되어 있는지 확인"""
    return bool(DEMO_ACCESS_KEY and DEMO_SECRET_KEY)


def check_trade_cooldown(user_id: int) -> str | None:
    """거래 쿨다운 확인. 위반 시 에러 메시지 반환, 통과 시 None"""
    now = time.time()
    last = _last_trade_time.get(user_id, 0)
    remaining = DEMO_TRADE_COOLDOWN_SEC - (now - last)
    if remaining > 0:
        return f"거래 쿨다운 중입니다. {remaining:.0f}초 후 다시 시도해주세요."
    return None


def check_daily_limit(user_id: int) -> str | None:
    """일일 거래 횟수 확인. 위반 시 에러 메시지 반환"""
    now = time.time()
    day_start = now - 86400
    # 24시간 이내 거래만 유지
    _trade_timestamps[user_id] = [
        t for t in _trade_timestamps[user_id] if t > day_start
    ]
    if len(_trade_timestamps[user_id]) >= DEMO_DAILY_TRADE_LIMIT:
        return f"일일 거래 한도({DEMO_DAILY_TRADE_LIMIT}회)를 초과했습니다."
    return None


def record_trade(user_id: int):
    """거래 기록 (쿨다운 및 일일 한도 추적용)"""
    now = time.time()
    _last_trade_time[user_id] = now
    _trade_timestamps[user_id].append(now)


def check_balance_limit(amount: float) -> str | None:
    """데모 잔고 상한 확인"""
    if amount > DEMO_MAX_BALANCE:
        return f"데모 잔고는 최대 {DEMO_MAX_BALANCE:,.0f}원까지 설정 가능합니다."
    return None
