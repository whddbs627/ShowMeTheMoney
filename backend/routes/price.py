from fastapi import APIRouter, Depends
from backend.engine import bot_manager
from backend.auth import get_current_user

router = APIRouter(tags=["price"])


@router.get("/price")
async def get_price(user: dict = Depends(get_current_user)):
    bot = bot_manager.get_bot(user["id"])
    if not bot:
        return {"coins": []}
    return {"coins": bot.get_status().get("coins", [])}
