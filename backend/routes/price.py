import asyncio
from fastapi import APIRouter, Depends
import pyupbit

from backend.engine import bot_manager
from backend.auth import get_current_user
from backend.database import get_watchlist
from strategy import calc_target_price, calc_rsi, check_ma_filter

router = APIRouter(tags=["price"])


async def _fetch_coin_data(ticker: str) -> dict:
    """봇 없이 직접 시세 조회"""
    try:
        price = await asyncio.to_thread(pyupbit.get_current_price, ticker)
        df_short = await asyncio.to_thread(pyupbit.get_ohlcv, ticker, interval="day", count=2)
        df_long = await asyncio.to_thread(pyupbit.get_ohlcv, ticker, interval="day", count=21)

        target = None
        rsi = None
        ma_bullish = None

        if df_short is not None and len(df_short) >= 2:
            target = float(calc_target_price(df_short, 0.5))
        if df_long is not None and len(df_long) >= 20:
            rsi = float(calc_rsi(df_long))
            ma_bullish = bool(check_ma_filter(df_long))

        return {
            "ticker": ticker,
            "state": "waiting",
            "current_price": float(price) if price else None,
            "target_price": target,
            "buy_price": None,
            "rsi": rsi,
            "ma_bullish": ma_bullish,
        }
    except Exception:
        return {
            "ticker": ticker, "state": "waiting",
            "current_price": None, "target_price": None,
            "buy_price": None, "rsi": None, "ma_bullish": None,
        }


@router.get("/price")
async def get_price(user: dict = Depends(get_current_user)):
    bot = bot_manager.get_bot(user["id"])

    # 봇이 실행 중이면 봇의 캐시된 데이터 사용
    if bot and bot.running:
        return {"coins": bot.get_status().get("coins", [])}

    # 봇이 꺼져있으면 watchlist 기반으로 직접 조회
    tickers = await get_watchlist(user["id"])
    if not tickers:
        return {"coins": []}

    # 보유 코인 정보 (봇이 있으면 trader에서, 없으면 무시)
    coins = []
    for ticker in tickers:
        data = await _fetch_coin_data(ticker)

        # 봇이 있으면 holding 상태 반영
        if bot and ticker in bot.traders:
            trader = bot.traders[ticker]
            if trader.holding:
                data["state"] = "holding"
                data["buy_price"] = trader.buy_price

        coins.append(data)
        await asyncio.sleep(0.1)  # rate limit

    return {"coins": coins}
