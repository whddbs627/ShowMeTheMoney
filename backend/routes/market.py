import asyncio
import time
from fastapi import APIRouter, Query
import pyupbit
import requests

router = APIRouter(tags=["market"])

# Cache (refresh every 60s)
_all_cache: list = []
_cache_ts: float = 0


@router.get("/market/coins")
async def search_coins(q: str = Query("", description="Search keyword")):
    from backend.coin_names import get_coin_name, get_all_names
    tickers = await asyncio.to_thread(pyupbit.get_tickers, fiat="KRW")
    if not tickers:
        return []

    if q:
        q_upper = q.upper()
        q_lower = q.lower()
        all_names = get_all_names()
        tickers = [
            t for t in tickers
            if q_upper in t.upper()
            or q_lower in all_names.get(t, {}).get("kr", "").lower()
            or q_lower in all_names.get(t, {}).get("en", "").lower()
        ]

    result = []
    for t in sorted(tickers):
        cn = get_coin_name(t)
        result.append({
            "ticker": t,
            "name": t.replace("KRW-", ""),
            "kr_name": cn["kr"],
            "en_name": cn["en"],
        })
    return result


def _fetch_all_tickers() -> list[dict]:
    from backend.coin_names import get_coin_name
    try:
        tickers = pyupbit.get_tickers(fiat="KRW")
        if not tickers:
            return []

        markets = ",".join(tickers)
        resp = requests.get(f"https://api.upbit.com/v1/ticker?markets={markets}", timeout=10)
        resp.raise_for_status()
        data = resp.json()

        results = []
        for item in data:
            ticker = item["market"]
            cn = get_coin_name(ticker)
            results.append({
                "ticker": ticker,
                "name": ticker.replace("KRW-", ""),
                "kr_name": cn["kr"],
                "current_price": item.get("trade_price", 0),
                "change_pct": round((item.get("signed_change_rate", 0)) * 100, 2),
                "volume_krw": round(item.get("acc_trade_price_24h", 0), 0),
            })
        return results
    except Exception:
        return []


async def _get_cached():
    global _all_cache, _cache_ts
    now = time.time()
    if now - _cache_ts < 60 and _all_cache:
        return _all_cache
    _all_cache = await asyncio.to_thread(_fetch_all_tickers)
    _cache_ts = now
    return _all_cache


@router.get("/market/top-gainers")
async def get_top_gainers(limit: int = Query(20, ge=1, le=50)):
    results = list(await _get_cached())
    results.sort(key=lambda x: x["change_pct"], reverse=True)
    return results[:limit]


@router.get("/market/top-volume")
async def get_top_volume(limit: int = Query(20, ge=1, le=50)):
    """거래대금 상위"""
    results = list(await _get_cached())
    results.sort(key=lambda x: x["volume_krw"], reverse=True)
    return results[:limit]


@router.get("/market/top-price")
async def get_top_price(limit: int = Query(20, ge=1, le=50)):
    """고가 코인"""
    results = list(await _get_cached())
    results.sort(key=lambda x: x["current_price"], reverse=True)
    return results[:limit]
