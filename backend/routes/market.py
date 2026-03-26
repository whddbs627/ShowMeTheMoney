import asyncio
import time
from fastapi import APIRouter, Query
import pyupbit
import requests

router = APIRouter(tags=["market"])

# Cache for top gainers (refresh every 60s)
_gainers_cache: list = []
_gainers_ts: float = 0


@router.get("/market/coins")
async def search_coins(q: str = Query("", description="Search keyword")):
    tickers = await asyncio.to_thread(pyupbit.get_tickers, fiat="KRW")
    if not tickers:
        return []

    if q:
        q_upper = q.upper()
        tickers = [t for t in tickers if q_upper in t.upper()]

    return [{"ticker": t, "name": t.replace("KRW-", "")} for t in sorted(tickers)]


def _fetch_all_tickers() -> list[dict]:
    """Upbit API로 전체 코인 정보를 한 번에 가져옴 (빠름)"""
    try:
        tickers = pyupbit.get_tickers(fiat="KRW")
        if not tickers:
            return []

        markets = ",".join(tickers)
        resp = requests.get(
            f"https://api.upbit.com/v1/ticker?markets={markets}",
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data:
            results.append({
                "ticker": item["market"],
                "name": item["market"].replace("KRW-", ""),
                "current_price": item.get("trade_price", 0),
                "change_pct": round((item.get("signed_change_rate", 0)) * 100, 2),
                "volume_krw": round(item.get("acc_trade_price_24h", 0), 0),
            })
        return results
    except Exception:
        return []


@router.get("/market/top-gainers")
async def get_top_gainers(limit: int = Query(20, ge=1, le=50)):
    global _gainers_cache, _gainers_ts

    now = time.time()
    if now - _gainers_ts < 60 and _gainers_cache:
        return _gainers_cache[:limit]

    results = await asyncio.to_thread(_fetch_all_tickers)
    results.sort(key=lambda x: x["change_pct"], reverse=True)
    _gainers_cache = results
    _gainers_ts = now
    return results[:limit]
