import asyncio
from fastapi import APIRouter, Depends
import pyupbit

from backend.engine import bot_manager
from backend.auth import get_current_user, decrypt_key
from backend.database import get_watchlist, get_demo_holdings
from strategy import calc_target_price, calc_rsi, check_ma_filter
from upbit_api import UpbitAPI

router = APIRouter(tags=["price"])

# 보유 상태 캐시 (API 실패 시 이전 상태 유지)
_holding_cache: dict[int, dict[str, dict]] = {}  # user_id -> {ticker -> {state, buy_price}}


async def _fetch_coin_data(ticker: str, api: UpbitAPI | None, user_k: float, user_id: int) -> dict:
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

        # 보유 여부 확인
        state = "waiting"
        buy_price = None
        if api:
            try:
                balance = await asyncio.to_thread(api.get_balance, ticker)
                if balance and balance > 0 and price and balance * price > 5000:
                    state = "holding"
                    avg = await asyncio.to_thread(api.get_avg_buy_price, ticker)
                    buy_price = avg
                # 캐시 업데이트
                if user_id not in _holding_cache:
                    _holding_cache[user_id] = {}
                _holding_cache[user_id][ticker] = {"state": state, "buy_price": buy_price}
            except Exception:
                # API 실패 시 캐시 사용
                cached = _holding_cache.get(user_id, {}).get(ticker)
                if cached:
                    state = cached["state"]
                    buy_price = cached["buy_price"]

        return {
            "ticker": ticker, "state": state,
            "current_price": float(price) if price else None,
            "target_price": target, "buy_price": buy_price,
            "rsi": rsi, "ma_bullish": ma_bullish,
        }
    except Exception:
        # 전체 실패 시 캐시 사용
        cached = _holding_cache.get(user_id, {}).get(ticker)
        return {
            "ticker": ticker,
            "state": cached["state"] if cached else "waiting",
            "current_price": None, "target_price": None,
            "buy_price": cached["buy_price"] if cached else None,
            "rsi": None, "ma_bullish": None,
        }


@router.get("/price")
async def get_price(user: dict = Depends(get_current_user)):
    bot = bot_manager.get_bot(user["id"])

    if bot and bot.running:
        status = bot.get_status()
        coins = status.get("coins", [])
        for coin in coins:
            if coin["state"] == "waiting" and bot.api:
                try:
                    bal = await asyncio.to_thread(bot.api.get_balance, coin["ticker"])
                    price = coin.get("current_price") or 0
                    if bal and bal > 0 and price and bal * price > 5000:
                        coin["state"] = "holding"
                        avg = await asyncio.to_thread(bot.api.get_avg_buy_price, coin["ticker"])
                        coin["buy_price"] = avg
                except Exception:
                    pass
        return {"coins": coins}

    tickers = await get_watchlist(user["id"])
    if not tickers:
        return {"coins": []}

    api = None
    enc_access = user.get("encrypted_access_key")
    enc_secret = user.get("encrypted_secret_key")
    if enc_access and enc_secret:
        try:
            api = UpbitAPI(decrypt_key(enc_access), decrypt_key(enc_secret))
        except Exception:
            pass

    user_k = user.get("strategy_k", 0.5)
    is_demo = bool(user.get("is_demo", 0))

    # 데모 모드: 가상 보유 상태
    demo_holdings = {}
    if is_demo:
        for h in await get_demo_holdings(user["id"]):
            demo_holdings[h["ticker"]] = h

    coins = []
    for ticker in tickers:
        if is_demo:
            # 데모 모드: 실제 잔고 대신 가상 보유 사용
            data = await _fetch_coin_data(ticker, None, user_k, user["id"])
            dh = demo_holdings.get(ticker)
            if dh and dh["volume"] > 0:
                data["state"] = "holding"
                data["buy_price"] = dh["avg_price"]
        else:
            data = await _fetch_coin_data(ticker, api, user_k, user["id"])
        coins.append(data)
        await asyncio.sleep(0.1)

    return {"coins": coins}


# 차트 데이터 API
@router.get("/chart/{ticker}")
async def get_chart(ticker: str, days: int = 30):
    try:
        df = await asyncio.to_thread(pyupbit.get_ohlcv, ticker, interval="day", count=days)
        if df is None or len(df) == 0:
            return []
        result = []
        for idx, row in df.iterrows():
            result.append({
                "date": idx.strftime("%m/%d"),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["volume"]),
            })
        return result
    except Exception:
        return []
