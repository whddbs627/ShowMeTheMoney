import re
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from backend.database import get_watchlist, add_to_watchlist, remove_from_watchlist
from backend.engine import bot_manager
from backend.auth import get_current_user

router = APIRouter(tags=["watchlist"])

TICKER_PATTERN = re.compile(r'^KRW-[A-Z0-9]{1,10}$')


class TickerRequest(BaseModel):
    ticker: str

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not TICKER_PATTERN.match(v):
            raise ValueError("Invalid ticker format (expected KRW-XXX)")
        return v


@router.get("/watchlist")
async def list_watchlist(user: dict = Depends(get_current_user)):
    tickers = await get_watchlist(user["id"])
    return {"tickers": tickers}


@router.post("/watchlist/add")
async def add_coin(req: TickerRequest, user: dict = Depends(get_current_user)):
    await add_to_watchlist(user["id"], req.ticker)
    bot = bot_manager.get_bot(user["id"])
    if bot and bot.running and req.ticker not in bot.tickers:
        bot.tickers.append(req.ticker)
        bot._add_coin(req.ticker)
    return {"message": f"Added {req.ticker}"}


@router.post("/watchlist/remove")
async def remove_coin(req: TickerRequest, user: dict = Depends(get_current_user)):
    await remove_from_watchlist(user["id"], req.ticker)
    bot = bot_manager.get_bot(user["id"])
    if bot and req.ticker in bot.tickers:
        bot.tickers.remove(req.ticker)
        bot._remove_coin(req.ticker)
    return {"message": f"Removed {req.ticker}"}
