import os
import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent.parent))

SERVER_START_TIME = str(int(time.time()))

from backend.database import init_db
from backend.engine import bot_manager
from backend.security import RateLimitMiddleware, ErrorHandlerMiddleware
from backend.routes import auth, bot, price, balance, trades, market, watchlist, leaderboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await bot_manager.stop_all()


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
