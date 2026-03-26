import sys
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from upbit_api import UpbitAPI
from strategy import should_buy, calc_target_price, calc_rsi, check_ma_filter
from trader import Trader
from notifier import Notifier
from backend.database import insert_trade, get_watchlist, add_to_watchlist, save_balance_snapshot
from backend.auth import decrypt_key

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))


class CoinState:
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.current_price: float | None = None
        self.target_price: float | None = None
        self.rsi: float | None = None
        self.ma_bullish: bool | None = None


class UserBot:
    def __init__(self, user_id: int, user: dict):
        self.user_id = user_id
        self.running = False
        self.task: asyncio.Task | None = None
        self.api: UpbitAPI | None = None
        self.notifier: Notifier | None = None
        self.traders: dict[str, Trader] = {}
        self.coin_states: dict[str, CoinState] = {}
        self.started_at: datetime | None = None
        self.tickers: list[str] = []
        self._loop_count = 0

        self.k = user.get("strategy_k", 0.5)
        self.use_ma = bool(user.get("strategy_ma", 1))
        self.use_rsi = bool(user.get("strategy_rsi", 1))
        self.rsi_lower = user.get("strategy_rsi_lower", 30.0)
        self.loss_pct = user.get("strategy_loss_pct", 0.03)
        self.max_investment = user.get("max_investment_krw", 100000)
        self.investment_ratio = 0.5

        # Notify settings
        self.notify_buy = bool(user.get("notify_buy", 1))
        self.notify_sell = bool(user.get("notify_sell", 1))
        self.notify_error = bool(user.get("notify_error", 1))
        self.notify_start_stop = bool(user.get("notify_start_stop", 1))

    def _init_components(self, access_key: str, secret_key: str, discord_url: str):
        self.api = UpbitAPI(access_key, secret_key)
        self.notifier = Notifier(discord_url)
        self.traders = {}
        self.coin_states = {}
        for ticker in self.tickers:
            self._add_coin(ticker)

    def _add_coin(self, ticker: str):
        if ticker in self.traders or not self.api:
            return
        self.traders[ticker] = Trader(
            api=self.api, notifier=self.notifier, ticker=ticker,
            investment_ratio=self.investment_ratio,
            max_investment_krw=self.max_investment, max_loss_pct=self.loss_pct,
        )
        self.coin_states[ticker] = CoinState(ticker)

    def _remove_coin(self, ticker: str):
        trader = self.traders.get(ticker)
        if trader and trader.holding:
            return
        self.traders.pop(ticker, None)
        self.coin_states.pop(ticker, None)

    async def _sync_holdings_to_watchlist(self):
        """보유 중인 코인을 watchlist에 자동 추가"""
        if not self.api:
            return
        try:
            balances = await asyncio.to_thread(self.api.upbit.get_balances)
            if not balances:
                return
            for b in balances:
                currency = b.get("currency", "")
                if currency == "KRW":
                    continue
                balance = float(b.get("balance", 0))
                avg_price = float(b.get("avg_buy_price", 0))
                if balance > 0 and avg_price > 0:
                    ticker = f"KRW-{currency}"
                    if ticker not in self.tickers:
                        self.tickers.append(ticker)
                        await add_to_watchlist(self.user_id, ticker)
                        self._add_coin(ticker)
                        self._log(f"[AUTO] Added holding {ticker} to watchlist")
        except Exception as e:
            logger.error(f"[User {self.user_id}] Sync holdings error: {e}")

    async def start(self, user: dict):
        if self.running:
            return

        enc_access = user.get("encrypted_access_key")
        enc_secret = user.get("encrypted_secret_key")
        if not enc_access or not enc_secret:
            raise ValueError("API keys not configured")

        access_key = decrypt_key(enc_access)
        secret_key = decrypt_key(enc_secret)
        discord_url = user.get("discord_webhook_url", "")

        self.tickers = await get_watchlist(self.user_id)

        self._init_components(access_key, secret_key, discord_url)

        # 보유 코인을 watchlist에 자동 추가
        await self._sync_holdings_to_watchlist()

        if not self.tickers:
            raise ValueError("Add coins to your watchlist first")

        for trader in self.traders.values():
            await asyncio.to_thread(trader.sync_position)

        self.running = True
        self.started_at = datetime.now(KST)
        self._loop_count = 0
        self.task = asyncio.create_task(self._loop())

        coins = ", ".join(self.tickers)
        self._log(f"[START] 봇 시작\n코인: {coins}", "start_stop")

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
        if self.notifier:
            self._log("[STOP] 봇 중지", "start_stop")

    def _log(self, msg: str, category: str = "info"):
        logger.info(f"[User {self.user_id}] {msg}")
        if not self.notifier:
            return
        should_send = (
            (category == "buy" and self.notify_buy) or
            (category == "sell" and self.notify_sell) or
            (category == "error" and self.notify_error) or
            (category == "start_stop" and self.notify_start_stop) or
            (category == "info")
        )
        if should_send:
            self.notifier.send(msg)

    async def _loop(self):
        while self.running:
            try:
                for ticker in list(self.tickers):
                    if not self.running:
                        break
                    await self._tick(ticker)
                    await asyncio.sleep(0.5)

                self._loop_count += 1
                # 매 30회(~5분)마다 balance 스냅샷 저장
                if self._loop_count % 30 == 0:
                    await self._save_balance()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._log(f"[ERROR] Bot loop: {e}", "error")
                await asyncio.sleep(60)
            await asyncio.sleep(10)

    async def _save_balance(self):
        try:
            krw = await asyncio.to_thread(self.api.get_krw_balance) or 0
            coin_value = 0
            for ticker in self.tickers:
                bal = await asyncio.to_thread(self.api.get_balance, ticker)
                price = await asyncio.to_thread(self.api.get_current_price, ticker)
                coin_value += (bal or 0) * (price or 0)
            total = krw + coin_value
            await save_balance_snapshot(self.user_id, krw, coin_value, total)
        except Exception as e:
            logger.error(f"[User {self.user_id}] Balance snapshot error: {e}")

    async def _tick(self, ticker: str):
        trader = self.traders.get(ticker)
        state = self.coin_states.get(ticker)
        if not trader or not state:
            return

        try:
            df_short = await asyncio.to_thread(self.api.get_ohlcv, ticker, "day", 2)
            df_long = await asyncio.to_thread(self.api.get_ohlcv, ticker, "day", 21)
            price = await asyncio.to_thread(self.api.get_current_price, ticker)

            if df_short is None or df_long is None or price is None:
                return

            state.current_price = float(price)
            state.target_price = float(calc_target_price(df_short, self.k))
            state.rsi = float(calc_rsi(df_long))
            state.ma_bullish = bool(check_ma_filter(df_long))

            if trader.holding:
                buy_price_snapshot = trader.buy_price
                buy_date_snapshot = trader.buy_date
                # 매도 전 잔고 확인 (매도 후에는 0이 됨)
                coin_bal = await asyncio.to_thread(self.api.get_balance, ticker) or 0
                sell_amount = coin_bal * price

                sold = await asyncio.to_thread(trader.check_and_sell, price)
                if sold:
                    pnl_pct = ((price - buy_price_snapshot) / buy_price_snapshot) * 100 if buy_price_snapshot > 0 else 0
                    pnl_krw = sell_amount * pnl_pct / 100

                    from datetime import timezone as tz, timedelta as td
                    trading_date = datetime.now(timezone(timedelta(hours=9)))
                    if trading_date.hour < 9:
                        trading_date_d = (trading_date - timedelta(days=1)).date()
                    else:
                        trading_date_d = trading_date.date()
                    reason = "NEXT_DAY" if buy_date_snapshot and trading_date_d > buy_date_snapshot else "STOP_LOSS"

                    await insert_trade(self.user_id, {
                        "timestamp": datetime.now(KST).isoformat(),
                        "side": "SELL", "ticker": ticker, "price": price,
                        "amount_krw": round(sell_amount, 0),
                        "volume": coin_bal,
                        "reason": reason,
                        "pnl_pct": round(pnl_pct, 2),
                        "pnl_krw": round(pnl_krw, 0),
                    })
            else:
                signal = should_buy(
                    df_short, df_long, price, self.k,
                    self.use_ma, self.use_rsi, self.rsi_lower,
                )
                if signal:
                    krw = await asyncio.to_thread(self.api.get_krw_balance)
                    amount = min((krw or 0) * self.investment_ratio, self.max_investment)
                    bought = await asyncio.to_thread(trader.check_and_buy, price, signal)
                    if bought:
                        volume = amount / price if price > 0 else 0
                        await insert_trade(self.user_id, {
                            "timestamp": datetime.now(KST).isoformat(),
                            "side": "BUY", "ticker": ticker, "price": price,
                            "amount_krw": round(amount, 0),
                            "volume": volume,
                            "reason": None, "pnl_pct": None, "pnl_krw": None,
                        })
        except Exception as e:
            self._log(f"[ERROR] [{ticker}] {e}", "error")

    def get_status(self) -> dict:
        uptime = (datetime.now(KST) - self.started_at).total_seconds() if self.started_at else None
        coins = []
        for ticker in self.tickers:
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
        return {"running": self.running, "uptime_seconds": uptime, "coins": coins}


class BotManager:
    def __init__(self):
        self.bots: dict[int, UserBot] = {}

    def get_bot(self, user_id: int) -> UserBot | None:
        return self.bots.get(user_id)

    def get_or_create_bot(self, user_id: int, user: dict) -> UserBot:
        if user_id not in self.bots:
            self.bots[user_id] = UserBot(user_id, user)
        return self.bots[user_id]

    async def stop_all(self):
        for bot in self.bots.values():
            await bot.stop()


bot_manager = BotManager()
