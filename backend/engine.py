import sys
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import config
from upbit_api import UpbitAPI
from strategy import should_buy, calc_target_price, calc_rsi, check_ma_filter
from trader import Trader
from notifier import Notifier
from backend.database import insert_trade

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))


class CoinState:
    """Per-coin cached state for API reads"""
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.current_price: float | None = None
        self.target_price: float | None = None
        self.rsi: float | None = None
        self.ma_bullish: bool | None = None


class BotEngine:
    def __init__(self):
        self.running = False
        self.task: asyncio.Task | None = None
        self.api: UpbitAPI | None = None
        self.notifier: Notifier | None = None
        self.traders: dict[str, Trader] = {}
        self.coin_states: dict[str, CoinState] = {}
        self.started_at: datetime | None = None

    def _init_components(self):
        self.api = UpbitAPI(config.UPBIT_ACCESS_KEY, config.UPBIT_SECRET_KEY)
        self.notifier = Notifier(config.DISCORD_WEBHOOK_URL)
        self.traders = {}
        self.coin_states = {}

        for ticker in config.TICKERS:
            self.traders[ticker] = Trader(
                api=self.api,
                notifier=self.notifier,
                ticker=ticker,
                investment_ratio=config.INVESTMENT_RATIO,
                max_investment_krw=config.MAX_INVESTMENT_KRW,
                max_loss_pct=config.MAX_LOSS_PCT,
            )
            self.coin_states[ticker] = CoinState(ticker)

    async def start(self):
        if self.running:
            return
        self._init_components()

        for ticker, trader in self.traders.items():
            await asyncio.to_thread(trader.sync_position)

        self.running = True
        self.started_at = datetime.now(KST)
        self.task = asyncio.create_task(self._loop())

        coins = ", ".join(config.TICKERS)
        self.notifier.send(f"[START] Bot started\nCoins: {coins}")
        logger.info(f"Bot engine started with {len(config.TICKERS)} coins")

    async def stop(self):
        if not self.running:
            return
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        self.task = None
        self.started_at = None
        self.notifier.send("[STOP] Bot stopped")
        logger.info("Bot engine stopped")

    async def _loop(self):
        while self.running:
            try:
                for ticker in config.TICKERS:
                    if not self.running:
                        break
                    await self._tick(ticker)
                    await asyncio.sleep(0.5)  # API rate limit buffer
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Bot loop error: {e}")
                await asyncio.sleep(60)
            await asyncio.sleep(config.CHECK_INTERVAL_SEC)

    async def _tick(self, ticker: str):
        trader = self.traders[ticker]
        state = self.coin_states[ticker]

        try:
            df_short = await asyncio.to_thread(self.api.get_ohlcv, ticker, "day", 2)
            df_long = await asyncio.to_thread(self.api.get_ohlcv, ticker, "day", 21)
            price = await asyncio.to_thread(self.api.get_current_price, ticker)

            if df_short is None or df_long is None or price is None:
                return

            state.current_price = price
            state.target_price = calc_target_price(df_short, config.K)
            state.rsi = calc_rsi(df_long)
            state.ma_bullish = check_ma_filter(df_long)

            if trader.holding:
                buy_price_snapshot = trader.buy_price
                buy_date_snapshot = trader.buy_date
                sold = await asyncio.to_thread(trader.check_and_sell, price)
                if sold:
                    pnl_pct = ((price - buy_price_snapshot) / buy_price_snapshot) * 100
                    now_date = datetime.now(KST).date()
                    reason = "NEXT_DAY" if buy_date_snapshot and now_date > buy_date_snapshot else "STOP_LOSS"
                    await insert_trade({
                        "timestamp": datetime.now(KST).isoformat(),
                        "side": "SELL",
                        "ticker": ticker,
                        "price": price,
                        "amount_krw": 0,
                        "reason": reason,
                        "pnl_pct": round(pnl_pct, 2),
                        "pnl_krw": 0,
                    })
            else:
                signal = should_buy(
                    df_short, df_long, price, config.K,
                    config.USE_MA_FILTER, config.USE_RSI_FILTER,
                    config.RSI_LOWER_BOUND,
                )
                if signal:
                    logger.info(f"[{ticker}] Buy signal at {price:,.0f} KRW")
                    krw_before = await asyncio.to_thread(self.api.get_krw_balance)
                    amount = min((krw_before or 0) * config.INVESTMENT_RATIO, config.MAX_INVESTMENT_KRW)
                    bought = await asyncio.to_thread(trader.check_and_buy, price, signal)
                    if bought:
                        await insert_trade({
                            "timestamp": datetime.now(KST).isoformat(),
                            "side": "BUY",
                            "ticker": ticker,
                            "price": price,
                            "amount_krw": round(amount, 0),
                            "reason": None,
                            "pnl_pct": None,
                            "pnl_krw": None,
                        })
        except Exception as e:
            logger.error(f"[{ticker}] Tick error: {e}")

    def get_status(self) -> dict:
        uptime = (datetime.now(KST) - self.started_at).total_seconds() if self.started_at else None

        coins = []
        for ticker in config.TICKERS:
            trader = self.traders.get(ticker)
            state = self.coin_states.get(ticker)
            coins.append({
                "ticker": ticker,
                "state": "holding" if trader and trader.holding else "waiting",
                "current_price": state.current_price if state else None,
                "target_price": state.target_price if state else None,
                "buy_price": trader.buy_price if trader and trader.holding else None,
                "rsi": state.rsi if state else None,
                "ma_bullish": state.ma_bullish if state else None,
            })

        return {
            "running": self.running,
            "uptime_seconds": uptime,
            "coins": coins,
        }


engine = BotEngine()
