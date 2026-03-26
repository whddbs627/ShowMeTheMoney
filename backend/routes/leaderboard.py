from fastapi import APIRouter
from backend.database import get_leaderboard

router = APIRouter(tags=["leaderboard"])


@router.get("/leaderboard")
async def leaderboard():
    return await get_leaderboard()
