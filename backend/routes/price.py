import asyncio
from fastapi import APIRouter, Depends
import pyupbit

from backend.engine import bot_manager
from backend.auth import get_current_user, decrypt_key
from backend.database import get_watchlist
from strategy import calc_target_price, calc_rsi, check_ma_filter
from upbit_api import UpbitAPI

router = APIRouter(tags=["price"])


async def _fetch_coin_data(ticker: str, api: UpbitAPI | None, user_k: float) -> dict:
    """코인 시세 + 보유 상태 조회"""
    try:
        price = await asyncio.to_thread(pyupbit.get_current_price, ticker)
        df_short = await asyncio.to_thread(pyupbit.get_ohlcv, ticker, interval="day", count=2)
        df_long = await asyncio.to_thread(pyupbit.get_ohlcv, ticker, interval="day", count=21)

        target = None
        rsi = None
        ma_bullish = None

        if df_short is not None and len(df_short) >= 2:
            target = float(calc_target_price(df_short, user_k))
        if df_long is not None and len(df_long) >= 20:
            rsi = float(calc_rsi(df_long))
            ma_bullish = bool(check_ma_filter(df_long))

        # 실제 업비트 잔고로 보유 여부 판단
        state = "waiting"
        buy_price = None
        if api:
            balance = await asyncio.to_thread(api.get_balance, ticker)
            if balance and balance > 0 and price and balance * price > 5000:
                state = "holding"
                avg = await asyncio.to_thread(api.get_avg_buy_price, ticker)
                buy_price = avg

        return {
            "ticker": ticker,
            "state": state,
            "current_price": float(price) if price else None,
            "target_price": target,
            "buy_price": buy_price,
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

    # 봇이 실행 중이면 봇의 캐시된 데이터 사용 (단, 잔고 기반 보유 상태 보정)
    if bot and bot.running:
        status = bot.get_status()
        # 봇 trader가 holding을 모르는 경우(수동 매수 등) 보정
        coins = status.get("coins", [])
        for coin in coins:
            if coin["state"] == "waiting" and bot.api:
                bal = await asyncio.to_thread(bot.api.get_balance, coin["ticker"])
                price = coin.get("current_price") or 0
                if bal and bal > 0 and price and bal * price > 5000:
                    coin["state"] = "holding"
                    avg = await asyncio.to_thread(bot.api.get_avg_buy_price, coin["ticker"])
                    coin["buy_price"] = avg
        return {"coins": coins}

    # 봇이 꺼져있으면 직접 조회
    tickers = await get_watchlist(user["id"])
    if not tickers:
        return {"coins": []}

    # API 생성
    api = None
    enc_access = user.get("encrypted_access_key")
    enc_secret = user.get("encrypted_secret_key")
    if enc_access and enc_secret:
        try:
            api = UpbitAPI(decrypt_key(enc_access), decrypt_key(enc_secret))
        except Exception:
            pass

    user_k = user.get("strategy_k", 0.5)

    coins = []
    for ticker in tickers:
        data = await _fetch_coin_data(ticker, api, user_k)
        coins.append(data)
        await asyncio.sleep(0.1)

    return {"coins": coins}
