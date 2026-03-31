"""API 엔드포인트 통합 테스트"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from backend.app import app
import backend.database as db_mod
import os


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    # 테스트용 DB/Redis 환경변수 (CI에서는 별도 설정 가능)
    db_url = os.getenv("TEST_DATABASE_URL", "postgresql://smtm:smtm@localhost:5432/showmethemoney_test")
    redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/1")
    os.environ["DATABASE_URL"] = db_url
    os.environ["REDIS_URL"] = redis_url

    await db_mod.init_db()
    yield

    # 테스트 후 테이블 초기화
    if db_mod.pool:
        async with db_mod.pool.acquire() as conn:
            for table in ["trades", "watchlist", "balance_snapshots", "demo_holdings", "coin_targets", "users"]:
                await conn.execute(f"TRUNCATE TABLE {table} CASCADE")
    if db_mod.redis_client:
        await db_mod.redis_client.flushdb()
    await db_mod.close_db()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", headers={"X-Test-Client": "1"}) as c:
        yield c


@pytest_asyncio.fixture
async def auth_client(client):
    res = await client.post("/api/auth/register", json={
        "username": "testuser", "password": "testpass123",
    })
    assert res.status_code == 200
    token = res.json()["token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


class TestAuth:
    async def test_register(self, client):
        res = await client.post("/api/auth/register", json={
            "username": "newuser", "password": "pass123456",
        })
        assert res.status_code == 200
        assert "token" in res.json()

    async def test_register_short_username(self, client):
        res = await client.post("/api/auth/register", json={
            "username": "ab", "password": "pass123456",
        })
        assert res.status_code == 400

    async def test_register_short_password(self, client):
        res = await client.post("/api/auth/register", json={
            "username": "testuser2", "password": "12345",
        })
        assert res.status_code == 400

    async def test_register_duplicate(self, client):
        await client.post("/api/auth/register", json={
            "username": "dupuser", "password": "pass123456",
        })
        res = await client.post("/api/auth/register", json={
            "username": "dupuser", "password": "pass123456",
        })
        assert res.status_code == 400

    async def test_login(self, client):
        await client.post("/api/auth/register", json={
            "username": "loginuser", "password": "pass123456",
        })
        res = await client.post("/api/auth/login", json={
            "username": "loginuser", "password": "pass123456",
        })
        assert res.status_code == 200
        assert "token" in res.json()

    async def test_login_wrong_password(self, client):
        await client.post("/api/auth/register", json={
            "username": "loginuser2", "password": "pass123456",
        })
        res = await client.post("/api/auth/login", json={
            "username": "loginuser2", "password": "wrong",
        })
        assert res.status_code == 401

    async def test_me(self, auth_client):
        res = await auth_client.get("/api/auth/me")
        assert res.status_code == 200
        data = res.json()
        assert data["username"] == "testuser"
        assert "strategy" in data

    async def test_unauthorized(self, client):
        res = await client.get("/api/auth/me")
        assert res.status_code in [401, 403]


class TestBot:
    async def test_status_no_bot(self, auth_client):
        res = await auth_client.get("/api/bot/status")
        assert res.status_code == 200
        assert res.json()["running"] is False

    async def test_start_no_keys(self, auth_client):
        res = await auth_client.post("/api/bot/start")
        assert res.status_code == 400


class TestWatchlist:
    async def test_empty_watchlist(self, auth_client):
        res = await auth_client.get("/api/watchlist")
        assert res.status_code == 200
        assert res.json()["tickers"] == []

    async def test_add_remove(self, auth_client):
        res = await auth_client.post("/api/watchlist/add", json={"ticker": "KRW-BTC"})
        assert res.status_code == 200

        res = await auth_client.get("/api/watchlist")
        assert "KRW-BTC" in res.json()["tickers"]

        res = await auth_client.post("/api/watchlist/remove", json={"ticker": "KRW-BTC"})
        assert res.status_code == 200

        res = await auth_client.get("/api/watchlist")
        assert "KRW-BTC" not in res.json()["tickers"]


class TestStrategy:
    async def test_save_strategy(self, auth_client):
        res = await auth_client.post("/api/auth/strategy", json={
            "k": 0.3, "use_ma": False, "use_rsi": True,
            "rsi_lower": 25, "loss_pct": 0.05, "take_profit_pct": 0.1,
            "max_investment_krw": 50000, "min_investment_krw": 5000,
            "strategy_type": "rsi_bounce",
        })
        assert res.status_code == 200

        res = await auth_client.get("/api/auth/me")
        s = res.json()["strategy"]
        assert s["k"] == 0.3
        assert s["strategy_type"] == "rsi_bounce"


class TestDemo:
    async def test_toggle_demo(self, auth_client):
        res = await auth_client.post("/api/demo/toggle", json={
            "is_demo": True, "demo_balance": 50000000,
        })
        assert res.status_code == 200

        res = await auth_client.get("/api/auth/me")
        assert res.json()["is_demo"] is True
        assert res.json()["demo_balance"] == 50000000

    async def test_demo_balance_limit(self, auth_client):
        res = await auth_client.post("/api/demo/toggle", json={
            "is_demo": True, "demo_balance": 99999999999,
        })
        assert res.status_code == 400


class TestVersion:
    async def test_version(self, client):
        res = await client.get("/api/version")
        assert res.status_code == 200
        assert "version" in res.json()


class TestLeaderboard:
    async def test_leaderboard(self, client):
        res = await client.get("/api/leaderboard")
        assert res.status_code == 200
        assert isinstance(res.json(), list)
