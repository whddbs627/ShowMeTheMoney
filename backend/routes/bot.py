from fastapi import APIRouter, Depends, HTTPException
from backend.engine import bot_manager
from backend.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bot"])


@router.get("/bot/status")
async def get_bot_status(user: dict = Depends(get_current_user)):
    bot = bot_manager.get_bot(user["id"])
    if not bot:
        return {"running": False, "uptime_seconds": None, "coins": []}
    return bot.get_status()


@router.post("/bot/start")
async def start_bot(user: dict = Depends(get_current_user)):
    if not user.get("encrypted_access_key"):
        raise HTTPException(400, "Please configure API keys in Settings first")

    try:
        bot = bot_manager.get_or_create_bot(user["id"], user)
        await bot.start(user)
        return {"message": "Bot started"}
    except Exception as e:
        logger.exception(f"Bot start failed for user {user['id']}")
        raise HTTPException(500, f"Bot start failed: {str(e)}")


@router.post("/bot/stop")
async def stop_bot(user: dict = Depends(get_current_user)):
    bot = bot_manager.get_bot(user["id"])
    if bot:
        await bot.stop()
    return {"message": "Bot stopped"}
