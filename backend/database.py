import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "trades.db"


async def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp   TEXT NOT NULL,
                side        TEXT NOT NULL,
                ticker      TEXT NOT NULL,
                price       REAL NOT NULL,
                amount_krw  REAL NOT NULL,
                reason      TEXT,
                pnl_pct     REAL,
                pnl_krw     REAL
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                ticker TEXT PRIMARY KEY
            )
        """)
        await db.commit()


async def insert_trade(trade: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO trades (timestamp, side, ticker, price, amount_krw, reason, pnl_pct, pnl_krw)
               VALUES (:timestamp, :side, :ticker, :price, :amount_krw, :reason, :pnl_pct, :pnl_krw)""",
            trade,
        )
        await db.commit()


async def get_trades(limit: int = 50, offset: int = 0) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM trades ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_cumulative_pnl() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT timestamp, pnl_krw,
                      SUM(COALESCE(pnl_krw, 0)) OVER (ORDER BY id) as cumulative_pnl_krw
               FROM trades
               WHERE side = 'SELL'
               ORDER BY id""",
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# Watchlist
async def get_watchlist() -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT ticker FROM watchlist ORDER BY ticker")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def add_to_watchlist(ticker: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO watchlist (ticker) VALUES (?)", (ticker,)
        )
        await db.commit()


async def remove_from_watchlist(ticker: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM watchlist WHERE ticker = ?", (ticker,))
        await db.commit()
