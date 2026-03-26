from fastapi import APIRouter
from backend.engine import engine
from backend.models import BotStatus

router = APIRouter(tags=["bot"])


@router.get("/bot/status", response_model=BotStatus)
async def get_bot_status():
    return engine.get_status()


@router.post("/bot/start")
async def start_bot():
    await engine.start()
    return {"message": "Bot started"}


@router.post("/bot/stop")
async def stop_bot():
    await engine.stop()
    return {"message": "Bot stopped"}
