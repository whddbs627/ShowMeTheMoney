import os
import json
import asyncpg
import redis.asyncio as aioredis

pool: asyncpg.Pool | None = None
redis_client: aioredis.Redis | None = None


async def init_db():
    global pool, redis_client

    database_url = os.getenv("DATABASE_URL", "postgresql://smtm:smtm@localhost:5432/showmethemoney")
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    pool = await asyncpg.create_pool(database_url, min_size=2, max_size=10)
    redis_client = aioredis.from_url(redis_url, decode_responses=True)

    async with pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id              SERIAL PRIMARY KEY,
                username        VARCHAR(100) UNIQUE NOT NULL,
                password_hash   TEXT NOT NULL,
                encrypted_access_key TEXT,
                encrypted_secret_key TEXT,
                discord_webhook_url  TEXT DEFAULT '',
                strategy_k      DOUBLE PRECISION DEFAULT 0.5,
                strategy_ma     INTEGER DEFAULT 1,
                strategy_rsi    INTEGER DEFAULT 1,
                strategy_rsi_lower DOUBLE PRECISION DEFAULT 30.0,
                strategy_loss_pct  DOUBLE PRECISION DEFAULT 0.03,
                max_investment_krw DOUBLE PRECISION DEFAULT 100000,
                min_investment_krw DOUBLE PRECISION DEFAULT 5000,
                notify_buy      INTEGER DEFAULT 1,
                notify_sell     INTEGER DEFAULT 1,
                notify_error    INTEGER DEFAULT 1,
                notify_start_stop INTEGER DEFAULT 1,
                take_profit_pct DOUBLE PRECISION DEFAULT 0.05,
                strategy_type   TEXT DEFAULT 'volatility_breakout',
                is_demo         INTEGER DEFAULT 0,
                demo_balance    DOUBLE PRECISION DEFAULT 10000000,
                created_at      TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        # Migrations for existing installations
        migrations = [
            ("min_investment_krw", "DOUBLE PRECISION DEFAULT 5000"),
            ("notify_buy", "INTEGER DEFAULT 1"),
            ("notify_sell", "INTEGER DEFAULT 1"),
            ("notify_error", "INTEGER DEFAULT 1"),
            ("notify_start_stop", "INTEGER DEFAULT 1"),
            ("take_profit_pct", "DOUBLE PRECISION DEFAULT 0.05"),
            ("strategy_type", "TEXT DEFAULT 'volatility_breakout'"),
            ("is_demo", "INTEGER DEFAULT 0"),
            ("demo_balance", "DOUBLE PRECISION DEFAULT 10000000"),
        ]
        for col, typedef in migrations:
            try:
                await conn.execute(f"ALTER TABLE users ADD COLUMN {col} {typedef}")
            except asyncpg.exceptions.DuplicateColumnError:
                pass
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id          SERIAL PRIMARY KEY,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                timestamp   TEXT NOT NULL,
                side        TEXT NOT NULL,
                ticker      TEXT NOT NULL,
                price       DOUBLE PRECISION NOT NULL,
                amount_krw  DOUBLE PRECISION NOT NULL,
                volume      DOUBLE PRECISION DEFAULT 0,
                reason      TEXT,
                pnl_pct     DOUBLE PRECISION,
                pnl_krw     DOUBLE PRECISION
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                user_id INTEGER NOT NULL REFERENCES users(id),
                ticker  TEXT NOT NULL,
                PRIMARY KEY (user_id, ticker)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS balance_snapshots (
                id          SERIAL PRIMARY KEY,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                timestamp   TEXT NOT NULL,
                krw_balance DOUBLE PRECISION DEFAULT 0,
                coin_value  DOUBLE PRECISION DEFAULT 0,
                total_krw   DOUBLE PRECISION DEFAULT 0
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS demo_holdings (
                user_id     INTEGER NOT NULL REFERENCES users(id),
                ticker      TEXT NOT NULL,
                volume      DOUBLE PRECISION DEFAULT 0,
                avg_price   DOUBLE PRECISION DEFAULT 0,
                PRIMARY KEY (user_id, ticker)
            )
        """)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS coin_targets (
                user_id     INTEGER NOT NULL REFERENCES users(id),
                ticker      TEXT NOT NULL,
                buy_target  DOUBLE PRECISION,
                stop_loss   DOUBLE PRECISION,
                take_profit DOUBLE PRECISION,
                PRIMARY KEY (user_id, ticker)
            )
        """)
        # Indexes
        for stmt in [
            "CREATE INDEX IF NOT EXISTS idx_trades_user_id ON trades(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_trades_timestamp ON trades(user_id, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_balance_snapshots_user_id ON balance_snapshots(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_demo_holdings_user_id ON demo_holdings(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_coin_targets_user_id ON coin_targets(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id)",
        ]:
            await conn.execute(stmt)


async def close_db():
    global pool, redis_client
    if pool:
        await pool.close()
        pool = None
    if redis_client:
        await redis_client.close()
        redis_client = None


# === Bot State (Redis) ===
async def save_bot_state(user_id: int, running: bool):
    if redis_client:
        await redis_client.hset("bot_state", str(user_id), "1" if running else "0")


async def get_running_bot_ids() -> list[int]:
    if not redis_client:
        return []
    data = await redis_client.hgetall("bot_state")
    return [int(uid) for uid, val in data.items() if val == "1"]


# === Users ===
async def create_user(username: str, password_hash: str) -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchval(
            "INSERT INTO users (username, password_hash) VALUES ($1, $2) RETURNING id",
            username, password_hash,
        )
        return row


async def get_user_by_username(username: str) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE username = $1", username)
        return dict(row) if row else None


async def get_user_by_id(user_id: int) -> dict | None:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT * FROM users WHERE id = $1", user_id)
        return dict(row) if row else None


async def delete_user(user_id: int):
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute("DELETE FROM trades WHERE user_id=$1", user_id)
            await conn.execute("DELETE FROM watchlist WHERE user_id=$1", user_id)
            await conn.execute("DELETE FROM balance_snapshots WHERE user_id=$1", user_id)
            await conn.execute("DELETE FROM demo_holdings WHERE user_id=$1", user_id)
            await conn.execute("DELETE FROM coin_targets WHERE user_id=$1", user_id)
            await conn.execute("DELETE FROM users WHERE id=$1", user_id)
    if redis_client:
        await redis_client.hdel("bot_state", str(user_id))


async def update_user_password(user_id: int, password_hash: str):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET password_hash=$1 WHERE id=$2", password_hash, user_id)


async def update_user_username(user_id: int, username: str):
    async with pool.acquire() as conn:
        await conn.execute("UPDATE users SET username=$1 WHERE id=$2", username, user_id)


async def update_user_keys(user_id: int, enc_access: str, enc_secret: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET encrypted_access_key=$1, encrypted_secret_key=$2 WHERE id=$3",
            enc_access, enc_secret, user_id,
        )


async def update_user_discord(user_id: int, webhook_url: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET discord_webhook_url=$1 WHERE id=$2",
            webhook_url, user_id,
        )


async def update_user_strategy(user_id: int, strategy: dict):
    async with pool.acquire() as conn:
        await conn.execute(
            """UPDATE users SET strategy_k=$1, strategy_ma=$2, strategy_rsi=$3,
               strategy_rsi_lower=$4, strategy_loss_pct=$5, max_investment_krw=$6, min_investment_krw=$7,
               take_profit_pct=$8, strategy_type=$9 WHERE id=$10""",
            strategy["k"], strategy["use_ma"], strategy["use_rsi"],
            strategy["rsi_lower"], strategy["loss_pct"],
            strategy.get("max_investment_krw", 100000),
            strategy.get("min_investment_krw", 5000),
            strategy.get("take_profit_pct", 0.05),
            strategy.get("strategy_type", "volatility_breakout"),
            user_id,
        )


async def update_user_notify_settings(user_id: int, buy: bool, sell: bool, error: bool, start_stop: bool):
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE users SET notify_buy=$1, notify_sell=$2, notify_error=$3, notify_start_stop=$4 WHERE id=$5",
            int(buy), int(sell), int(error), int(start_stop), user_id,
        )


# === Trades ===
async def insert_trade(user_id: int, trade: dict):
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO trades (user_id, timestamp, side, ticker, price, amount_krw, volume, reason, pnl_pct, pnl_krw)
               VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)""",
            user_id,
            trade["timestamp"], trade["side"], trade["ticker"],
            trade["price"], trade["amount_krw"], trade.get("volume", 0),
            trade.get("reason"), trade.get("pnl_pct"), trade.get("pnl_krw"),
        )
    # Invalidate leaderboard cache on new trade
    if redis_client:
        await redis_client.delete("leaderboard_cache")


async def get_trades(user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM trades WHERE user_id=$1 ORDER BY id DESC LIMIT $2 OFFSET $3",
            user_id, limit, offset,
        )
        return [dict(row) for row in rows]


async def get_cumulative_pnl(user_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """SELECT timestamp, pnl_krw,
                      SUM(COALESCE(pnl_krw, 0)) OVER (ORDER BY id) as cumulative_pnl_krw
               FROM trades WHERE user_id=$1 AND side='SELL' ORDER BY id""",
            user_id,
        )
        return [dict(row) for row in rows]


# === Balance Snapshots ===
async def save_balance_snapshot(user_id: int, krw: float, coin_value: float, total: float):
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO balance_snapshots (user_id, timestamp, krw_balance, coin_value, total_krw)
               VALUES ($1, NOW()::TEXT, $2, $3, $4)""",
            user_id, krw, coin_value, total,
        )


async def get_balance_history(user_id: int, limit: int = 100) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM balance_snapshots WHERE user_id=$1 ORDER BY id DESC LIMIT $2",
            user_id, limit,
        )
        return [dict(row) for row in rows]


# === Leaderboard (Redis-cached) ===
async def get_leaderboard() -> list[dict]:
    # Check Redis cache first
    if redis_client:
        cached = await redis_client.get("leaderboard_cache")
        if cached:
            return json.loads(cached)

    async with pool.acquire() as conn:
        rows = await conn.fetch("""
            SELECT u.username,
                   COUNT(t.id)::INTEGER as total_trades,
                   COALESCE(SUM(CASE WHEN t.side='SELL' THEN COALESCE(t.pnl_krw, 0) ELSE 0 END), 0)::DOUBLE PRECISION as total_pnl_krw,
                   AVG(CASE WHEN t.side='SELL' THEN t.pnl_pct END)::DOUBLE PRECISION as avg_pnl_pct
            FROM users u
            LEFT JOIN trades t ON u.id = t.user_id
            GROUP BY u.id, u.username
            HAVING COUNT(t.id) > 0
            ORDER BY SUM(CASE WHEN t.side='SELL' THEN COALESCE(t.pnl_krw, 0) ELSE 0 END) DESC
        """)
        result = [dict(row) for row in rows]

    # Cache for 60 seconds
    if redis_client:
        await redis_client.setex("leaderboard_cache", 60, json.dumps(result, default=str))

    return result


# === Watchlist ===
async def get_watchlist(user_id: int) -> list[str]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT ticker FROM watchlist WHERE user_id=$1 ORDER BY ticker", user_id,
        )
        return [row["ticker"] for row in rows]


async def add_to_watchlist(user_id: int, ticker: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO watchlist (user_id, ticker) VALUES ($1, $2) ON CONFLICT DO NOTHING",
            user_id, ticker,
        )


async def remove_from_watchlist(user_id: int, ticker: str):
    async with pool.acquire() as conn:
        await conn.execute(
            "DELETE FROM watchlist WHERE user_id=$1 AND ticker=$2", user_id, ticker,
        )


# === Demo Mode ===
async def update_demo_mode(user_id: int, is_demo: bool, demo_balance: float):
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE users SET is_demo=$1, demo_balance=$2 WHERE id=$3",
                int(is_demo), demo_balance, user_id,
            )
            if is_demo:
                await conn.execute("DELETE FROM demo_holdings WHERE user_id=$1", user_id)


async def get_demo_holdings(user_id: int) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM demo_holdings WHERE user_id=$1", user_id,
        )
        return [dict(row) for row in rows]


async def demo_buy(user_id: int, ticker: str, price: float, amount_krw: float):
    volume = amount_krw / price
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "UPDATE users SET demo_balance = demo_balance - $1 WHERE id=$2",
                amount_krw, user_id,
            )
            row = await conn.fetchrow(
                "SELECT volume, avg_price FROM demo_holdings WHERE user_id=$1 AND ticker=$2",
                user_id, ticker,
            )
            if row:
                old_vol, old_avg = row["volume"], row["avg_price"]
                new_vol = old_vol + volume
                new_avg = (old_vol * old_avg + volume * price) / new_vol
                await conn.execute(
                    "UPDATE demo_holdings SET volume=$1, avg_price=$2 WHERE user_id=$3 AND ticker=$4",
                    new_vol, new_avg, user_id, ticker,
                )
            else:
                await conn.execute(
                    "INSERT INTO demo_holdings (user_id, ticker, volume, avg_price) VALUES ($1,$2,$3,$4)",
                    user_id, ticker, volume, price,
                )


async def demo_sell(user_id: int, ticker: str, price: float) -> dict:
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT volume, avg_price FROM demo_holdings WHERE user_id=$1 AND ticker=$2",
                user_id, ticker,
            )
            if not row or row["volume"] <= 0:
                return {"error": "\uBCF4\uC720\uB7C9\uC774 \uC5C6\uC2B5\uB2C8\uB2E4"}
            volume, avg_price = row["volume"], row["avg_price"]
            sell_amount = volume * price
            pnl_pct = ((price - avg_price) / avg_price) * 100
            await conn.execute(
                "UPDATE users SET demo_balance = demo_balance + $1 WHERE id=$2",
                sell_amount, user_id,
            )
            await conn.execute(
                "DELETE FROM demo_holdings WHERE user_id=$1 AND ticker=$2",
                user_id, ticker,
            )
            return {"volume": volume, "avg_price": avg_price, "sell_amount": sell_amount, "pnl_pct": pnl_pct}


# === Coin Targets ===
async def get_coin_targets(user_id: int) -> dict[str, dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT * FROM coin_targets WHERE user_id=$1", user_id,
        )
        return {r["ticker"]: dict(r) for r in rows}


async def count_demo_users() -> int:
    async with pool.acquire() as conn:
        row = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_demo=1")
        return row or 0


async def set_coin_target(user_id: int, ticker: str, buy_target: float | None, stop_loss: float | None, take_profit: float | None):
    async with pool.acquire() as conn:
        await conn.execute(
            """INSERT INTO coin_targets (user_id, ticker, buy_target, stop_loss, take_profit)
               VALUES ($1, $2, $3, $4, $5)
               ON CONFLICT (user_id, ticker) DO UPDATE SET buy_target=$3, stop_loss=$4, take_profit=$5""",
            user_id, ticker, buy_target, stop_loss, take_profit,
        )
