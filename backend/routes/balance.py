import asyncio
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import pyupbit

from backend.engine import bot_manager
from backend.auth import get_current_user, decrypt_key
from backend.database import get_watchlist, insert_trade
from upbit_api import UpbitAPI
from datetime import datetime, timezone, timedelta

KST = timezone(timedelta(hours=9))
router = APIRouter(tags=["balance"])


def _get_api(user: dict) -> UpbitAPI:
    enc_access = user.get("encrypted_access_key")
    enc_secret = user.get("encrypted_secret_key")
    if not enc_access or not enc_secret:
        raise HTTPException(400, "API 키를 먼저 설정하세요")
    return UpbitAPI(decrypt_key(enc_access), decrypt_key(enc_secret))


@router.get("/balance")
async def get_balance(user: dict = Depends(get_current_user)):
    # 봇이 실행 중이면 봇의 API 사용
    bot = bot_manager.get_bot(user["id"])
    if bot and bot.api:
        api = bot.api
        tickers = bot.tickers
    else:
        # 봇 없으면 직접 API 생성
        try:
            api = _get_api(user)
        except HTTPException:
            return {"krw_balance": None, "coins": [], "total_krw": None}
        tickers = await get_watchlist(user["id"])

    krw = await asyncio.to_thread(api.get_krw_balance)
    total = krw or 0
    coins = []

    for ticker in tickers:
        balance = await asyncio.to_thread(api.get_balance, ticker)
        price = await asyncio.to_thread(api.get_current_price, ticker)
        value = (balance or 0) * (price or 0)
        total += value
        coins.append({
            "ticker": ticker, "balance": balance or 0,
            "price": price or 0, "value_krw": round(value, 0),
        })

    return {"krw_balance": krw, "coins": coins, "total_krw": round(total, 0)}


# === 수동 매수/매도 ===

class ManualOrderRequest(BaseModel):
    ticker: str
    amount_krw: float = 0  # 매수 시 사용 (원화)
    sell_all: bool = False  # 매도 시 전량 매도


@router.post("/order/buy")
async def manual_buy(req: ManualOrderRequest, user: dict = Depends(get_current_user)):
    api = _get_api(user)

    if req.amount_krw < 5000:
        raise HTTPException(400, "최소 주문 금액은 5,000원입니다")

    price = await asyncio.to_thread(api.get_current_price, req.ticker)
    if not price:
        raise HTTPException(400, f"{req.ticker} 가격 조회 실패")

    result = await asyncio.to_thread(api.buy_market, req.ticker, req.amount_krw)
    if result is None:
        raise HTTPException(500, "매수 주문 실패")

    volume = req.amount_krw / price
    await insert_trade(user["id"], {
        "timestamp": datetime.now(KST).isoformat(),
        "side": "BUY", "ticker": req.ticker, "price": price,
        "amount_krw": round(req.amount_krw, 0), "volume": volume,
        "reason": "MANUAL", "pnl_pct": None, "pnl_krw": None,
    })

    return {"message": f"{req.ticker} {req.amount_krw:,.0f}원 매수 완료", "price": price}


@router.post("/order/sell")
async def manual_sell(req: ManualOrderRequest, user: dict = Depends(get_current_user)):
    api = _get_api(user)

    balance = await asyncio.to_thread(api.get_balance, req.ticker)
    if not balance or balance <= 0:
        raise HTTPException(400, f"{req.ticker} 보유량이 없습니다")

    price = await asyncio.to_thread(api.get_current_price, req.ticker)
    if not price:
        raise HTTPException(400, f"{req.ticker} 가격 조회 실패")

    result = await asyncio.to_thread(api.sell_market, req.ticker, balance)
    if result is None:
        raise HTTPException(500, "매도 주문 실패")

    sell_amount = balance * price
    avg_buy = await asyncio.to_thread(api.get_avg_buy_price, req.ticker)
    pnl_pct = ((price - avg_buy) / avg_buy * 100) if avg_buy and avg_buy > 0 else 0
    pnl_krw = sell_amount * pnl_pct / 100

    await insert_trade(user["id"], {
        "timestamp": datetime.now(KST).isoformat(),
        "side": "SELL", "ticker": req.ticker, "price": price,
        "amount_krw": round(sell_amount, 0), "volume": balance,
        "reason": "MANUAL", "pnl_pct": round(pnl_pct, 2), "pnl_krw": round(pnl_krw, 0),
    })

    return {"message": f"{req.ticker} 전량 매도 완료", "price": price, "pnl_pct": round(pnl_pct, 2)}
