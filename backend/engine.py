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
from backend.database import (
    insert_trade, get_watchlist, add_to_watchlist, save_balance_snapshot,
    get_demo_holdings, demo_buy, demo_sell, get_user_by_id,
)
from backend.auth import decrypt_key
from backend.demo_guard import get_demo_api, check_trade_cooldown, check_daily_limit, record_trade

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
        self.is_demo = bool(user.get("is_demo", 0))
        self.demo_balance = user.get("demo_balance", 10000000)

        self.k = user.get("strategy_k", 0.5)
        self.use_ma = bool(user.get("strategy_ma", 1))
        self.use_rsi = bool(user.get("strategy_rsi", 1))
        self.rsi_lower = user.get("strategy_rsi_lower", 30.0)
        self.loss_pct = user.get("strategy_loss_pct", 0.03)
        self.max_investment = user.get("max_investment_krw", 100000)
        self.take_profit_pct = user.get("take_profit_pct", 0.05)
        self.strategy_type = user.get("strategy_type", "volatility_breakout")
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

    def _init_components_demo(self, demo_api: UpbitAPI, discord_url: str):
        """데모 모드 초기화: 공유 API로 시세만 조회"""
        self.api = demo_api
        self.notifier = Notifier(discord_url)
        self.traders = {}
        self.coin_states = {}
        for ticker in self.tickers:
            self._add_coin(ticker)

    async def _sync_demo_holdings(self):
        """데모 보유 코인 상태를 trader에 동기화"""
        holdings = await get_demo_holdings(self.user_id)
        for h in holdings:
            ticker = h["ticker"]
            if ticker not in self.tickers:
                self.tickers.append(ticker)
                await add_to_watchlist(self.user_id, ticker)
                self._add_coin(ticker)
            trader = self.traders.get(ticker)
            if trader and h["volume"] > 0:
                trader.holding = True
                trader.buy_price = h["avg_price"]
                trader.buy_date = trader._get_trading_date()
                trader.bought_today = True

    def _add_coin(self, ticker: str):
        if ticker in self.traders or not self.api:
            return
        self.traders[ticker] = Trader(
            api=self.api, notifier=self.notifier, ticker=ticker,
            investment_ratio=self.investment_ratio,
            max_investment_krw=self.max_investment, max_loss_pct=self.loss_pct,
            take_profit_pct=self.take_profit_pct,
        )
        self.coin_states[ticker] = CoinState(ticker)

    def _remove_coin(self, ticker: str):
        trader = self.traders.get(ticker)
        if trader and trader.holding:
            return
        self.traders.pop(ticker, None)
        self.coin_states.pop(ticker, None)

    async def _sync_holdings_to_watchlist(self):
        """보유 중인 코인을 watchlist에 자동 추가 + trader holding 상태 동기화"""
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
                    # watchlist에 없으면 추가
                    if ticker not in self.tickers:
                        self.tickers.append(ticker)
                        await add_to_watchlist(self.user_id, ticker)
                        self._add_coin(ticker)
                        self._log(f"[AUTO] 보유 코인 {ticker} 워치리스트에 추가", "info")

                    # trader의 holding 상태 동기화
                    trader = self.traders.get(ticker)
                    if trader and not trader.holding:
                        current_price = await asyncio.to_thread(self.api.get_current_price, ticker)
                        if current_price and balance * current_price > 5000:
                            trader.holding = True
                            trader.buy_price = avg_price
                            trader.buy_date = trader._get_trading_date()
                            trader.bought_today = True
                            logger.info(f"[User {self.user_id}] Synced holding: {ticker} avg={avg_price:,.0f}")
        except Exception as e:
            logger.error(f"[User {self.user_id}] Sync holdings error: {e}")

    async def start(self, user: dict):
        if self.running:
            return

        self.is_demo = bool(user.get("is_demo", 0))
        discord_url = user.get("discord_webhook_url", "")

        if self.is_demo:
            # 데모 모드: 서버 공유 API 키로 시세 조회
            demo_api = get_demo_api()
            if not demo_api:
                raise ValueError("서버에 데모용 API 키가 설정되지 않았습니다")
            self.tickers = await get_watchlist(self.user_id)
            self._init_components_demo(demo_api, discord_url)
            # 데모 보유 상태 동기화
            await self._sync_demo_holdings()
        else:
            # 실제 모드: 유저 개인 API 키
            enc_access = user.get("encrypted_access_key")
            enc_secret = user.get("encrypted_secret_key")
            if not enc_access or not enc_secret:
                raise ValueError("API keys not configured")
            access_key = decrypt_key(enc_access)
            secret_key = decrypt_key(enc_secret)
            self.tickers = await get_watchlist(self.user_id)
            self._init_components(access_key, secret_key, discord_url)
            # 보유 코인을 watchlist에 자동 추가
            await self._sync_holdings_to_watchlist()
            for trader in self.traders.values():
                await asyncio.to_thread(trader.sync_position)

        if not self.tickers:
            raise ValueError("Add coins to your watchlist first")

        self.running = True
        self.started_at = datetime.now(KST)
        self._loop_count = 0
        self.task = asyncio.create_task(self._loop())

        mode = "[가상] " if self.is_demo else ""
        coins = ", ".join(self.tickers)
        self._log(f"[START] {mode}봇 시작\n코인: {coins}", "start_stop")

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
            if self.is_demo:
                user = await get_user_by_id(self.user_id)
                krw = user.get("demo_balance", 0) if user else 0
                coin_value = 0
                holdings = await get_demo_holdings(self.user_id)
                for h in holdings:
                    price = await asyncio.to_thread(self.api.get_current_price, h["ticker"])
                    coin_value += h["volume"] * (price or 0)
            else:
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

            if self.is_demo:
                await self._tick_demo(ticker, trader, price)
            else:
                await self._tick_real(ticker, trader, price, df_short, df_long)

        except Exception as e:
            self._log(f"[ERROR] [{ticker}] {e}", "error")

    async def _tick_demo(self, ticker: str, trader: Trader, price: float):
        """데모 모드 매매 로직: DB 가상잔고 사용"""
        # 데모 보유 상태 동기화
        holdings = await get_demo_holdings(self.user_id)
        demo_h = next((h for h in holdings if h["ticker"] == ticker), None)

        if demo_h and demo_h["volume"] > 0:
            if not trader.holding:
                trader.holding = True
                trader.buy_price = demo_h["avg_price"]
                trader.buy_date = trader._get_trading_date()
                trader.bought_today = True

        if trader.holding:
            # 매도 조건 확인 (trader 내부 로직 재사용)
            buy_price_snapshot = trader.buy_price
            buy_date_snapshot = trader.buy_date
            trader._check_daily_reset()
            trading_date = trader._get_trading_date()

            is_new_day = buy_date_snapshot and trading_date > buy_date_snapshot
            is_stop_loss = price < buy_price_snapshot * (1 - self.loss_pct)
            is_take_profit = self.take_profit_pct > 0 and price > buy_price_snapshot * (1 + self.take_profit_pct)

            reason = None
            if is_take_profit:
                reason = "TAKE_PROFIT"
            elif is_new_day:
                reason = "NEXT_DAY"
            elif is_stop_loss:
                reason = "STOP_LOSS"

            if reason:
                result = await demo_sell(self.user_id, ticker, price)
                if "error" not in result:
                    pnl_pct = result.get("pnl_pct", 0)
                    sell_amount = result.get("sell_amount", 0)
                    trader.holding = False
                    trader.buy_price = 0.0
                    trader.bought_today = True
                    record_trade(self.user_id)

                    reason_kr = {"NEXT_DAY": "익일매도", "STOP_LOSS": "손절", "TAKE_PROFIT": "익절"}.get(reason, reason)
                    self._log(f"[가상매도 - {reason_kr}] {ticker} {price:,.0f}원 (수익률: {pnl_pct:+.2f}%)", "sell")

                    await insert_trade(self.user_id, {
                        "timestamp": datetime.now(KST).isoformat(),
                        "side": "SELL", "ticker": ticker, "price": price,
                        "amount_krw": round(sell_amount, 0),
                        "volume": result.get("volume", 0),
                        "reason": f"DEMO_{reason}",
                        "pnl_pct": round(pnl_pct, 2),
                        "pnl_krw": round(sell_amount * pnl_pct / 100, 0),
                    })
        else:
            # 매수 시그널 확인
            if trader.bought_today:
                return

            df_short = await asyncio.to_thread(self.api.get_ohlcv, ticker, "day", 2)
            df_long = await asyncio.to_thread(self.api.get_ohlcv, ticker, "day", 21)
            if df_short is None or df_long is None:
                return

            signal = should_buy(
                df_short, df_long, price, self.k,
                self.use_ma, self.use_rsi, self.rsi_lower,
                strategy_type=self.strategy_type,
            )
            if not signal:
                return

            # 쿨다운 확인
            if check_trade_cooldown(self.user_id) or check_daily_limit(self.user_id):
                return

            # 가상 잔고 확인
            user = await get_user_by_id(self.user_id)
            demo_bal = user.get("demo_balance", 0) if user else 0
            amount = min(demo_bal * self.investment_ratio, self.max_investment)
            if amount < 5000:
                return

            await demo_buy(self.user_id, ticker, price, amount)
            record_trade(self.user_id)
            trader.holding = True
            trader.buy_price = price
            trader.buy_date = trader._get_trading_date()
            trader.bought_today = True

            self._log(f"[가상매수] {ticker} {price:,.0f}원 ({amount:,.0f}원)", "buy")

            await insert_trade(self.user_id, {
                "timestamp": datetime.now(KST).isoformat(),
                "side": "BUY", "ticker": ticker, "price": price,
                "amount_krw": round(amount, 0),
                "volume": amount / price if price > 0 else 0,
                "reason": "DEMO", "pnl_pct": None, "pnl_krw": None,
            })

    async def _tick_real(self, ticker: str, trader: Trader, price: float, df_short, df_long):
        """실제 모드 매매 로직: Upbit API 사용"""
        # 수동 매수 등으로 trader가 holding을 모르는 경우 자동 sync
        if not trader.holding:
            bal = await asyncio.to_thread(self.api.get_balance, ticker)
            if bal and bal > 0 and price and bal * price > 5000:
                avg = await asyncio.to_thread(self.api.get_avg_buy_price, ticker)
                if avg and avg > 0:
                    trader.holding = True
                    trader.buy_price = avg
                    trader.buy_date = trader._get_trading_date()
                    trader.bought_today = True
                    logger.info(f"[User {self.user_id}] Auto-synced holding: {ticker} avg={avg:,.0f}")

        if trader.holding:
            buy_price_snapshot = trader.buy_price
            buy_date_snapshot = trader.buy_date
            coin_bal = await asyncio.to_thread(self.api.get_balance, ticker) or 0
            sell_amount = coin_bal * price

            sold = await asyncio.to_thread(trader.check_and_sell, price)
            if sold:
                pnl_pct = ((price - buy_price_snapshot) / buy_price_snapshot) * 100 if buy_price_snapshot > 0 else 0
                pnl_krw = sell_amount * pnl_pct / 100

                trading_date = datetime.now(KST)
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
                strategy_type=self.strategy_type,
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
        return {"running": self.running, "uptime_seconds": uptime, "coins": coins, "is_demo": self.is_demo}


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
