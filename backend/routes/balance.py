import asyncio
from fastapi import APIRouter

import config
from backend.engine import engine
from backend.models import BalanceInfo

router = APIRouter(tags=["balance"])


@router.get("/balance", response_model=BalanceInfo)
async def get_balance():
    if not engine.api:
        return BalanceInfo()

    krw = await asyncio.to_thread(engine.api.get_krw_balance)
    total = krw or 0

    coins = []
    for ticker in config.TICKERS:
        balance = await asyncio.to_thread(engine.api.get_balance, ticker)
        price = await asyncio.to_thread(engine.api.get_current_price, ticker)
        value = (balance or 0) * (price or 0)
        total += value
        coins.append({
            "ticker": ticker,
            "balance": balance or 0,
            "price": price or 0,
            "value_krw": round(value, 0),
        })

    return BalanceInfo(
        krw_balance=krw,
        coins=coins,
        total_krw=round(total, 0),
    )
