from fastapi import APIRouter, Query
from backend.database import get_trades, get_cumulative_pnl
from backend.models import TradeRecord, PnlPoint

router = APIRouter(tags=["trades"])


@router.get("/trades", response_model=list[TradeRecord])
async def list_trades(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0)):
    return await get_trades(limit, offset)


@router.get("/trades/pnl", response_model=list[PnlPoint])
async def get_pnl():
    return await get_cumulative_pnl()
