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

class BuyRequest(BaseModel):
    ticker: str
    amount_krw: float
    limit_price: float | None = None  # None이면 시장가


class SellRequest(BaseModel):
    ticker: str
    limit_price: float | None = None  # None이면 시장가 전량매도


@router.post("/order/buy")
async def manual_buy(req: BuyRequest, user: dict = Depends(get_current_user)):
    api = _get_api(user)

    if req.amount_krw < 5000:
        raise HTTPException(400, "최소 주문 금액은 5,000원입니다")

    price = await asyncio.to_thread(api.get_current_price, req.ticker)
    if not price:
        raise HTTPException(400, f"{req.ticker} 가격 조회 실패")

    if req.limit_price:
        # 지정가 매수
        volume = req.amount_krw / req.limit_price
        result = await asyncio.to_thread(api.buy_limit, req.ticker, req.limit_price, volume)
        order_price = req.limit_price
        msg = f"{req.ticker} 지정가 매수 주문 ({req.limit_price:,.0f}원 × {volume:.6f})"
    else:
        # 시장가 매수
        result = await asyncio.to_thread(api.buy_market, req.ticker, req.amount_krw)
        order_price = price
        msg = f"{req.ticker} {req.amount_krw:,.0f}원 시장가 매수 완료"

    if result is None:
        raise HTTPException(500, "매수 주문 실패")

    volume = req.amount_krw / order_price
    await insert_trade(user["id"], {
        "timestamp": datetime.now(KST).isoformat(),
        "side": "BUY", "ticker": req.ticker, "price": order_price,
        "amount_krw": round(req.amount_krw, 0), "volume": volume,
        "reason": "MANUAL_LIMIT" if req.limit_price else "MANUAL",
        "pnl_pct": None, "pnl_krw": None,
    })

    return {"message": msg, "price": order_price}


@router.post("/order/sell")
async def manual_sell(req: SellRequest, user: dict = Depends(get_current_user)):
    api = _get_api(user)

    balance = await asyncio.to_thread(api.get_balance, req.ticker)
    if not balance or balance <= 0:
        raise HTTPException(400, f"{req.ticker} 보유량이 없습니다")

    price = await asyncio.to_thread(api.get_current_price, req.ticker)
    if not price:
        raise HTTPException(400, f"{req.ticker} 가격 조회 실패")

    avg_buy = await asyncio.to_thread(api.get_avg_buy_price, req.ticker)

    if req.limit_price:
        # 지정가 매도
        result = await asyncio.to_thread(api.sell_limit, req.ticker, req.limit_price, balance)
        sell_price = req.limit_price
        msg = f"{req.ticker} 지정가 매도 주문 ({req.limit_price:,.0f}원 × {balance:.6f})"
    else:
        # 시장가 전량매도
        result = await asyncio.to_thread(api.sell_market, req.ticker, balance)
        sell_price = price
        msg = f"{req.ticker} 시장가 전량 매도 완료"

    if result is None:
        raise HTTPException(500, "매도 주문 실패")

    sell_amount = balance * sell_price
    pnl_pct = ((sell_price - avg_buy) / avg_buy * 100) if avg_buy and avg_buy > 0 else 0
    pnl_krw = sell_amount * pnl_pct / 100

    await insert_trade(user["id"], {
        "timestamp": datetime.now(KST).isoformat(),
        "side": "SELL", "ticker": req.ticker, "price": sell_price,
        "amount_krw": round(sell_amount, 0), "volume": balance,
        "reason": "MANUAL_LIMIT" if req.limit_price else "MANUAL",
        "pnl_pct": round(pnl_pct, 2), "pnl_krw": round(pnl_krw, 0),
    })

    return {"message": msg, "price": sell_price, "pnl_pct": round(pnl_pct, 2)}


# === 미체결 주문 ===

@router.get("/orders")
async def get_open_orders(user: dict = Depends(get_current_user)):
    api = _get_api(user)
    orders = await asyncio.to_thread(api.get_open_orders)
    result = []
    for o in orders:
        result.append({
            "uuid": o.get("uuid"),
            "side": "매수" if o.get("side") == "bid" else "매도",
            "ticker": o.get("market", ""),
            "price": float(o.get("price", 0)),
            "volume": float(o.get("volume", 0)),
            "remaining": float(o.get("remaining_volume", 0)),
            "amount_krw": round(float(o.get("price", 0)) * float(o.get("volume", 0)), 0),
            "created_at": o.get("created_at", ""),
        })
    return result


class CancelRequest(BaseModel):
    uuid: str


@router.post("/orders/cancel")
async def cancel_order(req: CancelRequest, user: dict = Depends(get_current_user)):
    api = _get_api(user)
    result = await asyncio.to_thread(api.cancel_order, req.uuid)
    if result is None:
        raise HTTPException(500, "주문 취소 실패")
    return {"message": "주문이 취소되었습니다"}
