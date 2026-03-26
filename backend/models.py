from pydantic import BaseModel


class CoinStatus(BaseModel):
    ticker: str
    state: str  # "holding" | "waiting"
    current_price: float | None = None
    target_price: float | None = None
    buy_price: float | None = None
    rsi: float | None = None
    ma_bullish: bool | None = None


class BotStatus(BaseModel):
    running: bool
    uptime_seconds: float | None = None
    coins: list[CoinStatus] = []


class BalanceInfo(BaseModel):
    krw_balance: float | None = None
    coins: list[dict] = []
    total_krw: float | None = None


class TradeRecord(BaseModel):
    id: int
    timestamp: str
    side: str
    ticker: str
    price: float
    amount_krw: float
    reason: str | None = None
    pnl_pct: float | None = None
    pnl_krw: float | None = None


class PnlPoint(BaseModel):
    timestamp: str
    cumulative_pnl_krw: float
