from fastapi import APIRouter, Query, Depends
from backend.database import get_trades, get_cumulative_pnl
from backend.auth import get_current_user

router = APIRouter(tags=["trades"])


@router.get("/trades")
async def list_trades(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user: dict = Depends(get_current_user),
):
    return await get_trades(user["id"], limit, offset)


@router.get("/trades/pnl")
async def get_pnl(user: dict = Depends(get_current_user)):
    return await get_cumulative_pnl(user["id"])
