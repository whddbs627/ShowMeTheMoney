import aiosqlite
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "trades.db"


async def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                username        TEXT UNIQUE NOT NULL,
                password_hash   TEXT NOT NULL,
                encrypted_access_key TEXT,
                encrypted_secret_key TEXT,
                discord_webhook_url  TEXT DEFAULT '',
                strategy_k      REAL DEFAULT 0.5,
                strategy_ma     INTEGER DEFAULT 1,
                strategy_rsi    INTEGER DEFAULT 1,
                strategy_rsi_lower REAL DEFAULT 30.0,
                strategy_loss_pct  REAL DEFAULT 0.03,
                max_investment_krw REAL DEFAULT 100000,
                created_at      TEXT DEFAULT (datetime('now'))
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                timestamp   TEXT NOT NULL,
                side        TEXT NOT NULL,
                ticker      TEXT NOT NULL,
                price       REAL NOT NULL,
                amount_krw  REAL NOT NULL,
                reason      TEXT,
                pnl_pct     REAL,
                pnl_krw     REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id INTEGER NOT NULL,
                ticker  TEXT NOT NULL,
                PRIMARY KEY (user_id, ticker),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        await db.commit()


# === Users ===
async def create_user(username: str, password_hash: str) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password_hash),
        )
        await db.commit()
        return cursor.lastrowid


async def get_user_by_username(username: str) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None


async def update_user_keys(user_id: int, enc_access: str, enc_secret: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET encrypted_access_key=?, encrypted_secret_key=? WHERE id=?",
            (enc_access, enc_secret, user_id),
        )
        await db.commit()


async def update_user_discord(user_id: int, webhook_url: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET discord_webhook_url=? WHERE id=?",
            (webhook_url, user_id),
        )
        await db.commit()


async def update_user_strategy(user_id: int, strategy: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """UPDATE users SET strategy_k=?, strategy_ma=?, strategy_rsi=?,
               strategy_rsi_lower=?, strategy_loss_pct=?, max_investment_krw=? WHERE id=?""",
            (
                strategy["k"], strategy["use_ma"], strategy["use_rsi"],
                strategy["rsi_lower"], strategy["loss_pct"], strategy["max_investment_krw"],
                user_id,
            ),
        )
        await db.commit()


# === Trades ===
async def insert_trade(user_id: int, trade: dict):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO trades (user_id, timestamp, side, ticker, price, amount_krw, reason, pnl_pct, pnl_krw)
               VALUES (?, :timestamp, :side, :ticker, :price, :amount_krw, :reason, :pnl_pct, :pnl_krw)""",
            (user_id, *[trade[k] for k in ["timestamp", "side", "ticker", "price", "amount_krw", "reason", "pnl_pct", "pnl_krw"]]),
        )
        await db.commit()


async def get_trades(user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            "SELECT * FROM trades WHERE user_id=? ORDER BY id DESC LIMIT ? OFFSET ?",
            (user_id, limit, offset),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


async def get_cumulative_pnl(user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute(
            """SELECT timestamp, pnl_krw,
                      SUM(COALESCE(pnl_krw, 0)) OVER (ORDER BY id) as cumulative_pnl_krw
               FROM trades WHERE user_id=? AND side='SELL' ORDER BY id""",
            (user_id,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# === Leaderboard ===
async def get_leaderboard() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("""
            SELECT u.username,
                   COUNT(t.id) as total_trades,
                   SUM(CASE WHEN t.side='SELL' THEN COALESCE(t.pnl_krw, 0) ELSE 0 END) as total_pnl_krw,
                   AVG(CASE WHEN t.side='SELL' THEN t.pnl_pct END) as avg_pnl_pct
            FROM users u
            LEFT JOIN trades t ON u.id = t.user_id
            GROUP BY u.id
            HAVING total_trades > 0
            ORDER BY total_pnl_krw DESC
        """)
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


# === Watchlist ===
async def get_watchlist(user_id: int) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT ticker FROM watchlist WHERE user_id=? ORDER BY ticker", (user_id,)
        )
        rows = await cursor.fetchall()
        return [row[0] for row in rows]


async def add_to_watchlist(user_id: int, ticker: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, ticker) VALUES (?, ?)",
            (user_id, ticker),
        )
        await db.commit()


async def remove_from_watchlist(user_id: int, ticker: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM watchlist WHERE user_id=? AND ticker=?", (user_id, ticker)
        )
        await db.commit()
