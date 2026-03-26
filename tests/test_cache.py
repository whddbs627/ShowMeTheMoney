"""캐시 레이어 테스트"""
import asyncio
import pytest
from backend.upbit_cache import UpbitCache


class TestUpbitCache:
    def test_set_get(self):
        cache = UpbitCache(ttl_seconds=10)
        cache.set("key1", 100)
        assert cache.get("key1") == 100

    def test_get_missing(self):
        cache = UpbitCache(ttl_seconds=10)
        assert cache.get("nonexistent") is None

    def test_none_not_cached(self):
        cache = UpbitCache(ttl_seconds=10)
        cache.set("key1", None)
        assert cache.get("key1") is None

    def test_expiry(self):
        cache = UpbitCache(ttl_seconds=0.1)
        cache.set("key1", "value")
        assert cache._is_valid("key1") is True

        import time
        time.sleep(0.2)
        assert cache._is_valid("key1") is False
        # 만료되어도 get은 반환 (fallback용)
        assert cache.get("key1") == "value"

    @pytest.mark.asyncio
    async def test_get_or_fetch(self):
        cache = UpbitCache(ttl_seconds=10)
        call_count = 0

        def fetch():
            nonlocal call_count
            call_count += 1
            return 42

        # 첫 호출: fetch 실행
        result = await cache.get_or_fetch("key1", fetch)
        assert result == 42
        assert call_count == 1

        # 두 번째 호출: 캐시 반환 (fetch 안 함)
        result = await cache.get_or_fetch("key1", fetch)
        assert result == 42
        assert call_count == 1

    @pytest.mark.asyncio
    async def test_fetch_failure_returns_cache(self):
        cache = UpbitCache(ttl_seconds=0.1)
        cache.set("key1", "old_value")

        import time
        time.sleep(0.2)  # 만료

        def failing_fetch():
            raise Exception("API error")

        result = await cache.get_or_fetch("key1", failing_fetch)
        assert result == "old_value"  # 만료된 캐시 반환

    def test_clear_user(self):
        cache = UpbitCache(ttl_seconds=10)
        cache.set("u1:bal:BTC", 100)
        cache.set("u1:avg:BTC", 50000)
        cache.set("u2:bal:BTC", 200)
        cache.set("price:BTC", 60000)

        cache.clear_user(1)

        assert cache.get("u1:bal:BTC") is None
        assert cache.get("u1:avg:BTC") is None
        assert cache.get("u2:bal:BTC") == 200  # 다른 유저 유지
        assert cache.get("price:BTC") == 60000  # 글로벌 캐시 유지
