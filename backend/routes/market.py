import asyncio
from fastapi import APIRouter, Query
import pyupbit

router = APIRouter(tags=["market"])


@router.get("/market/coins")
async def search_coins(q: str = Query("", description="Search keyword")):
    """업비트 KRW 마켓 코인 검색"""
    tickers = await asyncio.to_thread(pyupbit.get_tickers, fiat="KRW")
    if not tickers:
        return []

    if q:
        q_upper = q.upper()
        tickers = [t for t in tickers if q_upper in t.upper()]

    return [{"ticker": t, "name": t.replace("KRW-", "")} for t in sorted(tickers)]


@router.get("/market/top-gainers")
async def get_top_gainers(limit: int = Query(20, ge=1, le=50)):
    """24시간 상승률 상위 코인 추천"""
    tickers = await asyncio.to_thread(pyupbit.get_tickers, fiat="KRW")
    if not tickers:
        return []

    # 전체 현재가 + 전일 종가 조회
    prices = await asyncio.to_thread(pyupbit.get_current_price, tickers)
    if not prices:
        return []

    results = []
    for ticker in tickers:
        try:
            current = prices.get(ticker)
            if not current:
                continue

            # 개별 OHLCV로 전일 종가 가져오기
            df = await asyncio.to_thread(pyupbit.get_ohlcv, ticker, interval="day", count=2)
            if df is None or len(df) < 2:
                continue

            prev_close = df.iloc[-2]["close"]
            if prev_close <= 0:
                continue

            change_pct = ((current - prev_close) / prev_close) * 100

            results.append({
                "ticker": ticker,
                "name": ticker.replace("KRW-", ""),
                "current_price": current,
                "prev_close": prev_close,
                "change_pct": round(change_pct, 2),
            })

            await asyncio.sleep(0.1)  # rate limit
        except Exception:
            continue

    results.sort(key=lambda x: x["change_pct"], reverse=True)
    return results[:limit]
