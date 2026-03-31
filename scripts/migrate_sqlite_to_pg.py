"""
기존 SQLite 데이터를 PostgreSQL + Redis로 마이그레이션하는 스크립트.

사용법:
    python scripts/migrate_sqlite_to_pg.py

환경변수:
    DATABASE_URL  - PostgreSQL 연결 URL (기본: postgresql://smtm:smtm@localhost:5432/showmethemoney)
    REDIS_URL     - Redis 연결 URL (기본: redis://localhost:6379/0)
    SQLITE_PATH   - SQLite DB 파일 경로 (기본: data/trades.db)
"""
import asyncio
import os
import sqlite3
import sys
from pathlib import Path

import asyncpg
import redis.asyncio as aioredis

SQLITE_PATH = os.getenv("SQLITE_PATH", str(Path(__file__).parent.parent / "data" / "trades.db"))
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://smtm:smtm@localhost:5432/showmethemoney")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")


async def migrate():
    if not Path(SQLITE_PATH).exists():
        print(f"SQLite DB not found: {SQLITE_PATH}")
        sys.exit(1)

    # SQLite 연결
    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    # PostgreSQL 연결
    pg_conn = await asyncpg.connect(DATABASE_URL)
    redis_client = aioredis.from_url(REDIS_URL, decode_responses=True)

    try:
        # 1. init_db를 먼저 실행해서 테이블 생성
        sys.path.insert(0, str(Path(__file__).parent.parent))
        os.environ["DATABASE_URL"] = DATABASE_URL
        os.environ["REDIS_URL"] = REDIS_URL
        from backend.database import init_db, close_db
        await init_db()

        # 2. users 마이그레이션
        print("Migrating users...")
        cursor = sqlite_conn.execute("SELECT * FROM users")
        users = cursor.fetchall()
        for u in users:
            u = dict(u)
            await pg_conn.execute(
                """INSERT INTO users (id, username, password_hash, encrypted_access_key, encrypted_secret_key,
                   discord_webhook_url, strategy_k, strategy_ma, strategy_rsi, strategy_rsi_lower,
                   strategy_loss_pct, max_investment_krw, min_investment_krw, notify_buy, notify_sell,
                   notify_error, notify_start_stop, take_profit_pct, strategy_type, is_demo, demo_balance)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)
                   ON CONFLICT (id) DO NOTHING""",
                u["id"], u["username"], u["password_hash"],
                u.get("encrypted_access_key"), u.get("encrypted_secret_key"),
                u.get("discord_webhook_url", ""),
                u.get("strategy_k", 0.5), u.get("strategy_ma", 1), u.get("strategy_rsi", 1),
                u.get("strategy_rsi_lower", 30.0), u.get("strategy_loss_pct", 0.03),
                u.get("max_investment_krw", 100000), u.get("min_investment_krw", 5000),
                u.get("notify_buy", 1), u.get("notify_sell", 1),
                u.get("notify_error", 1), u.get("notify_start_stop", 1),
                u.get("take_profit_pct", 0.05), u.get("strategy_type", "volatility_breakout"),
                u.get("is_demo", 0), u.get("demo_balance", 10000000),
            )
        print(f"  -> {len(users)} users migrated")

        # 3. trades 마이그레이션
        print("Migrating trades...")
        cursor = sqlite_conn.execute("SELECT * FROM trades")
        trades = cursor.fetchall()
        for t in trades:
            t = dict(t)
            await pg_conn.execute(
                """INSERT INTO trades (id, user_id, timestamp, side, ticker, price, amount_krw, volume, reason, pnl_pct, pnl_krw)
                   VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11)
                   ON CONFLICT (id) DO NOTHING""",
                t["id"], t["user_id"], t["timestamp"], t["side"], t["ticker"],
                t["price"], t["amount_krw"], t.get("volume", 0),
                t.get("reason"), t.get("pnl_pct"), t.get("pnl_krw"),
            )
        print(f"  -> {len(trades)} trades migrated")

        # 4. watchlist 마이그레이션
        print("Migrating watchlist...")
        cursor = sqlite_conn.execute("SELECT * FROM watchlist")
        watchlist = cursor.fetchall()
        for w in watchlist:
            w = dict(w)
            await pg_conn.execute(
                "INSERT INTO watchlist (user_id, ticker) VALUES ($1, $2) ON CONFLICT DO NOTHING",
                w["user_id"], w["ticker"],
            )
        print(f"  -> {len(watchlist)} watchlist entries migrated")

        # 5. balance_snapshots 마이그레이션
        print("Migrating balance_snapshots...")
        cursor = sqlite_conn.execute("SELECT * FROM balance_snapshots")
        snapshots = cursor.fetchall()
        for s in snapshots:
            s = dict(s)
            await pg_conn.execute(
                """INSERT INTO balance_snapshots (id, user_id, timestamp, krw_balance, coin_value, total_krw)
                   VALUES ($1,$2,$3,$4,$5,$6)
                   ON CONFLICT (id) DO NOTHING""",
                s["id"], s["user_id"], s["timestamp"],
                s.get("krw_balance", 0), s.get("coin_value", 0), s.get("total_krw", 0),
            )
        print(f"  -> {len(snapshots)} balance snapshots migrated")

        # 6. demo_holdings 마이그레이션
        print("Migrating demo_holdings...")
        cursor = sqlite_conn.execute("SELECT * FROM demo_holdings")
        holdings = cursor.fetchall()
        for h in holdings:
            h = dict(h)
            await pg_conn.execute(
                """INSERT INTO demo_holdings (user_id, ticker, volume, avg_price)
                   VALUES ($1,$2,$3,$4)
                   ON CONFLICT DO NOTHING""",
                h["user_id"], h["ticker"], h.get("volume", 0), h.get("avg_price", 0),
            )
        print(f"  -> {len(holdings)} demo holdings migrated")

        # 7. coin_targets 마이그레이션
        print("Migrating coin_targets...")
        cursor = sqlite_conn.execute("SELECT * FROM coin_targets")
        targets = cursor.fetchall()
        for ct in targets:
            ct = dict(ct)
            await pg_conn.execute(
                """INSERT INTO coin_targets (user_id, ticker, buy_target, stop_loss, take_profit)
                   VALUES ($1,$2,$3,$4,$5)
                   ON CONFLICT DO NOTHING""",
                ct["user_id"], ct["ticker"],
                ct.get("buy_target"), ct.get("stop_loss"), ct.get("take_profit"),
            )
        print(f"  -> {len(targets)} coin targets migrated")

        # 8. bot_state -> Redis 마이그레이션
        print("Migrating bot_state to Redis...")
        try:
            cursor = sqlite_conn.execute("SELECT * FROM bot_state")
            bot_states = cursor.fetchall()
            for bs in bot_states:
                bs = dict(bs)
                await redis_client.hset("bot_state", str(bs["user_id"]), str(bs.get("running", 0)))
            print(f"  -> {len(bot_states)} bot states migrated to Redis")
        except sqlite3.OperationalError:
            print("  -> bot_state table not found, skipping")

        # 9. PostgreSQL 시퀀스 리셋
        print("Resetting sequences...")
        for table, seq in [
            ("users", "users_id_seq"),
            ("trades", "trades_id_seq"),
            ("balance_snapshots", "balance_snapshots_id_seq"),
        ]:
            max_id = await pg_conn.fetchval(f"SELECT COALESCE(MAX(id), 0) FROM {table}")
            if max_id > 0:
                await pg_conn.execute(f"SELECT setval('{seq}', {max_id})")
                print(f"  -> {seq} set to {max_id}")

        print("\nMigration complete!")

    finally:
        sqlite_conn.close()
        await pg_conn.close()
        await redis_client.close()
        await close_db()


if __name__ == "__main__":
    asyncio.run(migrate())
