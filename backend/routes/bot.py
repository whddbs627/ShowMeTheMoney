import aiosqlite
from fastapi import APIRouter, Depends, HTTPException
from backend.engine import bot_manager
from backend.auth import get_current_user
from backend.database import DB_PATH
import logging

logger = logging.getLogger(__name__)
router = APIRouter(tags=["bot"])


async def _save_bot_state(user_id: int, running: bool):
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS bot_state (
                    user_id INTEGER PRIMARY KEY, running INTEGER DEFAULT 0
                )
            """)
            await db.execute(
                "INSERT OR REPLACE INTO bot_state (user_id, running) VALUES (?, ?)",
                (user_id, int(running)),
            )
            await db.commit()
    except Exception:
        pass


@router.get("/bot/status")
async def get_bot_status(user: dict = Depends(get_current_user)):
    bot = bot_manager.get_bot(user["id"])
    if not bot:
        return {"running": False, "uptime_seconds": None, "coins": []}
    return bot.get_status()


@router.post("/bot/start")
async def start_bot(user: dict = Depends(get_current_user)):
    is_demo = bool(user.get("is_demo", 0))

    if not is_demo and not user.get("encrypted_access_key"):
        raise HTTPException(400, "설정에서 API 키를 먼저 입력해주세요")

    if is_demo:
        from backend.demo_guard import has_demo_api
        if not has_demo_api():
            raise HTTPException(400, "서버에 데모용 API 키가 설정되지 않았습니다")

    try:
        bot = bot_manager.get_or_create_bot(user["id"], user)
        await bot.start(user)
        await _save_bot_state(user["id"], True)
        return {"message": "봇이 시작되었습니다"}
    except Exception as e:
        logger.exception(f"Bot start failed for user {user['id']}")
        raise HTTPException(500, f"봇 시작 실패: {str(e)}")


@router.post("/bot/stop")
async def stop_bot(user: dict = Depends(get_current_user)):
    bot = bot_manager.get_bot(user["id"])
    if bot:
        await bot.stop()
    await _save_bot_state(user["id"], False)
    return {"message": "봇이 중지되었습니다"}
