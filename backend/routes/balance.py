import asyncio
from fastapi import APIRouter, Depends

from backend.engine import bot_manager
from backend.auth import get_current_user

router = APIRouter(tags=["balance"])


@router.get("/balance")
async def get_balance(user: dict = Depends(get_current_user)):
    bot = bot_manager.get_bot(user["id"])
    if not bot or not bot.api:
        return {"krw_balance": None, "coins": [], "total_krw": None}

    krw = await asyncio.to_thread(bot.api.get_krw_balance)
    total = krw or 0
    coins = []

    for ticker in bot.tickers:
        balance = await asyncio.to_thread(bot.api.get_balance, ticker)
        price = await asyncio.to_thread(bot.api.get_current_price, ticker)
        value = (balance or 0) * (price or 0)
        total += value
        coins.append({
            "ticker": ticker, "balance": balance or 0,
            "price": price or 0, "value_krw": round(value, 0),
        })

    return {"krw_balance": krw, "coins": coins, "total_krw": round(total, 0)}
