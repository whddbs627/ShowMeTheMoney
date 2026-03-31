import os
import sys
import time
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent.parent))

SERVER_START_TIME = str(int(time.time()))

from backend.database import init_db, close_db, get_running_bot_ids, get_user_by_id
from backend.engine import bot_manager
from backend.security import RateLimitMiddleware, ErrorHandlerMiddleware
from backend.routes import auth, bot, price, balance, trades, market, watchlist, leaderboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # 코인 이름 로드
    from backend.coin_names import _load as load_names
    load_names()
    # 이전에 실행 중이던 봇 복원
    await _restore_bots()
    yield
    await bot_manager.stop_all()
    await close_db()


async def _restore_bots():
    """서버 재시작 시 이전 봇 상태 복원"""
    _logger = logging.getLogger(__name__)
    try:
        running_ids = await get_running_bot_ids()

        for uid in running_ids:
            user = await get_user_by_id(uid)
            if not user:
                continue
            # 실제 유저: API 키 필요, 데모 유저: 공유 API 키 사용
            is_demo = bool(user.get("is_demo", 0))
            has_keys = bool(user.get("encrypted_access_key"))
            if has_keys or is_demo:
                try:
                    bot = bot_manager.get_or_create_bot(uid, user)
                    await bot.start(user)
                    mode = "demo" if is_demo else "real"
                    _logger.info(f"Restored {mode} bot for user {uid}")
                except Exception as e:
                    _logger.error(f"Failed to restore bot for user {uid}: {e}")
    except Exception as e:
        _logger.error(f"Bot restore failed: {e}")


app = FastAPI(title="ShowMeTheMoney", lifespan=lifespan)

# 미들웨어 (순서 중요: 아래가 먼저 실행)
app.add_middleware(ErrorHandlerMiddleware)
app.add_middleware(RateLimitMiddleware, max_requests=120, window_seconds=60)
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(bot.router, prefix="/api")
app.include_router(price.router, prefix="/api")
app.include_router(balance.router, prefix="/api")
app.include_router(trades.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
app.include_router(leaderboard.router, prefix="/api")


@app.get("/api/version")
async def get_version():
    return {"version": SERVER_START_TIME}
