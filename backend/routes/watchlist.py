from fastapi import APIRouter
from pydantic import BaseModel
from backend.database import get_watchlist, add_to_watchlist, remove_from_watchlist
from backend.engine import engine
import config

router = APIRouter(tags=["watchlist"])


class TickerRequest(BaseModel):
    ticker: str


@router.get("/watchlist")
async def list_watchlist():
    tickers = await get_watchlist()
    return {"tickers": tickers}


@router.post("/watchlist/add")
async def add_coin(req: TickerRequest):
    await add_to_watchlist(req.ticker)

    # 봇이 실행 중이면 동적으로 추가
    if engine.running and req.ticker not in config.TICKERS:
        config.TICKERS.append(req.ticker)
        engine._add_coin(req.ticker)

    return {"message": f"Added {req.ticker}"}


@router.post("/watchlist/remove")
async def remove_coin(req: TickerRequest):
    await remove_from_watchlist(req.ticker)

    # 봇에서도 제거
    if req.ticker in config.TICKERS:
        config.TICKERS.remove(req.ticker)
        engine._remove_coin(req.ticker)

    return {"message": f"Removed {req.ticker}"}
