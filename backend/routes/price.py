import re
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query
import pyupbit

from backend.engine import bot_manager
from backend.auth import get_current_user, decrypt_key
from backend.database import get_watchlist, get_demo_holdings
from backend.upbit_cache import price_cache, balance_cache, ohlcv_cache
from backend.demo_guard import get_demo_api, has_demo_api
from strategy import calc_target_price, calc_rsi, check_ma_filter
from upbit_api import UpbitAPI
from backend.coin_names import get_coin_name

router = APIRouter(tags=["price"])


async def _cached_price(ticker: str) -> float | None:
    return await price_cache.get_or_fetch(f"price:{ticker}", pyupbit.get_current_price, ticker)


async def _cached_ohlcv(ticker: str, interval: str, count: int):
    key = f"ohlcv:{ticker}:{interval}:{count}"
    return await ohlcv_cache.get_or_fetch(key, pyupbit.get_ohlcv, ticker, interval, count)


async def _cached_balance(api: UpbitAPI, ticker: str, user_id: int) -> float:
    return await balance_cache.get_or_fetch(f"u{user_id}:bal:{ticker}", api.get_balance, ticker) or 0


async def _cached_avg_price(api: UpbitAPI, ticker: str, user_id: int) -> float:
    return await balance_cache.get_or_fetch(f"u{user_id}:avg:{ticker}", api.get_avg_buy_price, ticker) or 0


async def _build_coin_data(ticker: str, api: UpbitAPI | None, user_k: float, user_id: int) -> dict:
    price = await _cached_price(ticker)
    df_short = await _cached_ohlcv(ticker, "day", 2)
    df_long = await _cached_ohlcv(ticker, "day", 21)

    target = None
    rsi = None
    ma_bullish = None

    try:
        if df_short is not None and len(df_short) >= 2:
            target = float(calc_target_price(df_short, user_k))
        if df_long is not None and len(df_long) >= 20:
            rsi = float(calc_rsi(df_long))
            ma_bullish = bool(check_ma_filter(df_long))
    except Exception:
        pass

    state = "waiting"
    buy_price = None

    if api:
        bal = await _cached_balance(api, ticker, user_id)
        if bal > 0 and price and bal * price > 5000:
            state = "holding"
            buy_price = await _cached_avg_price(api, ticker, user_id)

    cn = get_coin_name(ticker)
    return {
        "ticker": ticker, "state": state,
        "kr_name": cn["kr"],
        "current_price": float(price) if price else None,
        "target_price": target, "buy_price": buy_price,
        "rsi": rsi, "ma_bullish": ma_bullish,
    }


@router.get("/price")
async def get_price(user: dict = Depends(get_current_user)):
    bot = bot_manager.get_bot(user["id"])

    # 봇 실행 중: 봇 캐시 + 잔고 보정
    if bot and bot.running and bot.api:
        status = bot.get_status()
        coins = status.get("coins", [])
        for coin in coins:
            if coin["state"] == "waiting":
                bal = await _cached_balance(bot.api, coin["ticker"], user["id"])
                price = coin.get("current_price") or 0
                if bal > 0 and price and bal * price > 5000:
                    coin["state"] = "holding"
                    coin["buy_price"] = await _cached_avg_price(bot.api, coin["ticker"], user["id"])
        return {"coins": coins}

    # 봇 정지: 직접 조회
    tickers = await get_watchlist(user["id"])
    if not tickers:
        return {"coins": []}

    is_demo = bool(user.get("is_demo", 0))

    api = None
    if not is_demo:
        enc_access = user.get("encrypted_access_key")
        enc_secret = user.get("encrypted_secret_key")
        if enc_access and enc_secret:
            try:
                api = UpbitAPI(decrypt_key(enc_access), decrypt_key(enc_secret))
            except Exception:
                pass

    user_k = user.get("strategy_k", 0.5)

    # 데모 보유 상태
    demo_holdings = {}
    if is_demo:
        for h in await get_demo_holdings(user["id"]):
            demo_holdings[h["ticker"]] = h

    coins = []
    for ticker in tickers:
        data = await _build_coin_data(ticker, api if not is_demo else None, user_k, user["id"])
        if is_demo:
            dh = demo_holdings.get(ticker)
            if dh and dh["volume"] > 0:
                data["state"] = "holding"
                data["buy_price"] = dh["avg_price"]
        coins.append(data)

    return {"coins": coins}


TICKER_PATTERN = re.compile(r'^KRW-[A-Z0-9]{1,10}$')
VALID_INTERVALS = {"minute1", "minute3", "minute5", "minute10", "minute15", "minute30", "minute60", "minute240", "day", "week", "month"}


# 차트 데이터 API
@router.get("/chart/{ticker}")
async def get_chart(ticker: str, interval: str = "day", count: int = Query(30, ge=1, le=200)):
    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(400, "Invalid ticker format")
    if interval not in VALID_INTERVALS:
        raise HTTPException(400, f"Invalid interval. Must be one of: {', '.join(sorted(VALID_INTERVALS))}")
    try:
        df = await _cached_ohlcv(ticker, interval, count)
        if df is None or len(df) == 0:
            return []

        fmt = "%m/%d %H:%M" if "minute" in interval else "%m/%d"
        return [
            {
                "date": idx.strftime(fmt),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            }
            for idx, row in df.iterrows()
        ]
    except Exception:
        return []
