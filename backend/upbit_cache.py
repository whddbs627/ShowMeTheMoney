"""
Upbit API 응답 캐시 레이어 (Redis 기반)
- 가격, 잔고, OHLCV 데이터를 TTL 기반으로 캐싱
- 업비트 rate limit (초당 10회) 보호
- 여러 유저가 같은 코인 조회 시 1번만 API 호출
- API 실패 시 이전 캐시 반환
- Redis 장애 시 인메모리 fallback
"""
import time
import json
import asyncio
import logging
from typing import Any

import backend.database as db_mod

logger = logging.getLogger(__name__)


def _serialize(value: Any) -> str:
    """캐시 값을 JSON 문자열로 직렬화"""
    if hasattr(value, "to_json"):
        # pandas DataFrame
        return json.dumps({"__df__": True, "data": value.to_json()})
    return json.dumps(value, default=str)


def _deserialize(raw: str) -> Any:
    """JSON 문자열을 캐시 값으로 역직렬화"""
    import pandas as pd
    obj = json.loads(raw)
    if isinstance(obj, dict) and obj.get("__df__"):
        return pd.read_json(obj["data"])
    return obj


class UpbitCache:
    def __init__(self, ttl_seconds: float = 5.0, prefix: str = "upbit"):
        self._local: dict[str, tuple[float, Any]] = {}  # 인메모리 fallback
        self._ttl = ttl_seconds
        self._prefix = prefix
        self._lock = asyncio.Lock()

    def _redis_key(self, key: str) -> str:
        return f"{self._prefix}:{key}"

    def _local_is_valid(self, key: str) -> bool:
        if key not in self._local:
            return False
        ts, _ = self._local[key]
        return (time.time() - ts) < self._ttl

    def get(self, key: str) -> Any | None:
        """동기 로컬 캐시 조회 (fallback용)"""
        entry = self._local.get(key)
        if entry is None:
            return None
        return entry[1]

    def set(self, key: str, value: Any):
        """로컬 캐시에 저장"""
        if value is not None:
            self._local[key] = (time.time(), value)

    async def _redis_get(self, key: str) -> Any | None:
        """Redis에서 캐시 조회"""
        rc = db_mod.redis_client
        if not rc:
            return None
        try:
            raw = await rc.get(self._redis_key(key))
            if raw:
                return _deserialize(raw)
        except Exception as e:
            logger.debug(f"Redis get failed for {key}: {e}")
        return None

    async def _redis_set(self, key: str, value: Any):
        """Redis에 캐시 저장"""
        rc = db_mod.redis_client
        if not rc or value is None:
            return
        try:
            ttl_ms = int(self._ttl * 1000)
            await rc.psetex(self._redis_key(key), ttl_ms, _serialize(value))
        except Exception as e:
            logger.debug(f"Redis set failed for {key}: {e}")

    async def get_or_fetch(self, key: str, fetch_fn, *args) -> Any:
        """캐시에 있으면 반환, 없으면 fetch 후 캐시 (Redis + 로컬)"""
        # 1. 로컬 캐시 확인
        if self._local_is_valid(key):
            return self._local[key][1]

        # 2. Redis 캐시 확인 (다른 유저가 이미 캐싱했을 수 있음)
        redis_val = await self._redis_get(key)
        if redis_val is not None:
            self.set(key, redis_val)  # 로컬에도 저장
            return redis_val

        # 3. API 호출
        try:
            value = await asyncio.to_thread(fetch_fn, *args)
            if value is not None:
                self.set(key, value)
                await self._redis_set(key, value)
                return value
        except Exception as e:
            logger.debug(f"Cache fetch failed for {key}: {e}")

        # 4. 실패 시 만료된 로컬 캐시라도 반환
        return self.get(key)

    def clear_user(self, user_id: int):
        """유저 관련 캐시 삭제"""
        keys_to_delete = [k for k in self._local if k.startswith(f"u{user_id}:")]
        for k in keys_to_delete:
            del self._local[k]


# 글로벌 캐시 인스턴스
price_cache = UpbitCache(ttl_seconds=5.0, prefix="upbit:price")     # 가격: 5초
balance_cache = UpbitCache(ttl_seconds=10.0, prefix="upbit:bal")    # 잔고: 10초
ohlcv_cache = UpbitCache(ttl_seconds=60.0, prefix="upbit:ohlcv")   # OHLCV: 60초
