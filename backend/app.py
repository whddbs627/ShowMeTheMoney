import sys
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.database import init_db
from backend.engine import engine
from backend.routes import bot, price, balance, trades, market, watchlist


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await engine.stop()


app = FastAPI(title="ShowMeTheMoney", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(bot.router, prefix="/api")
app.include_router(price.router, prefix="/api")
app.include_router(balance.router, prefix="/api")
app.include_router(trades.router, prefix="/api")
app.include_router(market.router, prefix="/api")
app.include_router(watchlist.router, prefix="/api")
