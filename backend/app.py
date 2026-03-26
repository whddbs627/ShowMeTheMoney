import sys
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

sys.path.insert(0, str(Path(__file__).parent.parent))

# 서버 시작 시간 (프론트 자동 새로고침용)
SERVER_START_TIME = str(int(time.time()))

from backend.database import init_db
from backend.engine import bot_manager
from backend.routes import auth, bot, price, balance, trades, market, watchlist, leaderboard


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await bot_manager.stop_all()


app = FastAPI(title="ShowMeTheMoney", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
