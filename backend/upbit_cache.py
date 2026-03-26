"""
Upbit API 응답 캐시 레이어
- 가격, 잔고, OHLCV 데이터를 TTL 기반으로 캐싱
- 업비트 rate limit (초당 10회) 보호
- API 실패 시 이전 캐시 반환
"""
import time
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class UpbitCache:
    def __init__(self, ttl_seconds: float = 5.0):
        self._cache: dict[str, tuple[float, Any]] = {}  # key -> (timestamp, value)
        self._ttl = ttl_seconds
        self._lock = asyncio.Lock()

    def _is_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        ts, _ = self._cache[key]
        return (time.time() - ts) < self._ttl

    def get(self, key: str) -> Any | None:
        entry = self._cache.get(key)
        if entry is None:
            return None
        return entry[1]

    def set(self, key: str, value: Any):
        if value is not None:
            self._cache[key] = (time.time(), value)

    async def get_or_fetch(self, key: str, fetch_fn, *args) -> Any:
        """캐시에 있으면 반환, 없으면 fetch 후 캐시"""
        if self._is_valid(key):
            return self._cache[key][1]

        try:
            value = await asyncio.to_thread(fetch_fn, *args)
            if value is not None:
                self.set(key, value)
                return value
        except Exception as e:
            logger.debug(f"Cache fetch failed for {key}: {e}")

        # 실패 시 만료된 캐시라도 반환
        return self.get(key)

    def clear_user(self, user_id: int):
        """유저 관련 캐시 삭제"""
        keys_to_delete = [k for k in self._cache if k.startswith(f"u{user_id}:")]
        for k in keys_to_delete:
            del self._cache[k]


# 글로벌 캐시 인스턴스
price_cache = UpbitCache(ttl_seconds=5.0)     # 가격: 5초
balance_cache = UpbitCache(ttl_seconds=10.0)  # 잔고: 10초
ohlcv_cache = UpbitCache(ttl_seconds=60.0)    # OHLCV: 60초
