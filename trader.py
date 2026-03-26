import logging
from datetime import datetime, timezone, timedelta

from upbit_api import UpbitAPI
from notifier import Notifier

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))


class Trader:
    def __init__(
        self,
        api: UpbitAPI,
        notifier: Notifier,
        ticker: str,
        investment_ratio: float,
        max_investment_krw: float,
        max_loss_pct: float,
    ):
        self.api = api
        self.notifier = notifier
        self.ticker = ticker
        self.investment_ratio = investment_ratio
        self.max_investment_krw = max_investment_krw
        self.max_loss_pct = max_loss_pct

        self.holding = False
        self.buy_price = 0.0
        self.buy_date = None  # KST date when bought

    def sync_position(self):
        """재시작 시 기존 보유 포지션 확인 (크래시 복구)"""
        balance = self.api.get_balance(self.ticker)
        if balance and balance > 0:
            avg_price = self.api.get_avg_buy_price(self.ticker)
            current_price = self.api.get_current_price(self.ticker)

            if avg_price and current_price and balance * current_price > 5000:
                self.holding = True
                self.buy_price = avg_price
                self.buy_date = datetime.now(KST).date()
                logger.info(
                    f"Synced existing position: {self.ticker} "
                    f"balance={balance:.8f}, avg_price={avg_price:,.0f}"
                )
                return

        self.holding = False
        logger.info("No existing position found")

    def check_and_buy(self, current_price: float, should_buy: bool) -> bool:
        """매수 조건 확인 및 주문 실행"""
        if self.holding:
            return False

        if not should_buy:
            return False

        krw_balance = self.api.get_krw_balance()
        if krw_balance is None:
            return False

        amount = min(krw_balance * self.investment_ratio, self.max_investment_krw)

        # 업비트 최소 주문: 5,000 KRW
        if amount < 5000:
            logger.warning(f"Insufficient KRW balance: {amount:,.0f}")
            return False

        result = self.api.buy_market(self.ticker, amount)
        if result is None:
            return False

        self.holding = True
        self.buy_price = current_price
        self.buy_date = datetime.now(KST).date()

        msg = (
            f"[BUY] {self.ticker}\n"
            f"Price: {current_price:,.0f} KRW\n"
            f"Amount: {amount:,.0f} KRW"
        )
        self.notifier.send(msg)
        return True

    def check_and_sell(self, current_price: float) -> bool:
        """매도 조건 확인 및 주문 실행"""
        if not self.holding:
            return False

        now_kst = datetime.now(KST)
        is_new_day = self.buy_date and now_kst.date() > self.buy_date
        is_stop_loss = current_price < self.buy_price * (1 - self.max_loss_pct)

        reason = None
        if is_new_day:
            reason = "NEXT_DAY"
        elif is_stop_loss:
            reason = "STOP_LOSS"
        else:
            return False

        balance = self.api.get_balance(self.ticker)
        if not balance or balance <= 0:
            logger.warning("No coin balance to sell")
            self.holding = False
            return False

        result = self.api.sell_market(self.ticker, balance)
        if result is None:
            return False

        pnl_pct = ((current_price - self.buy_price) / self.buy_price) * 100
        self.holding = False

        msg = (
            f"[SELL - {reason}] {self.ticker}\n"
            f"Buy: {self.buy_price:,.0f} -> Sell: {current_price:,.0f} KRW\n"
            f"P&L: {pnl_pct:+.2f}%"
        )
        self.notifier.send(msg)
        self.buy_price = 0.0
        self.buy_date = None
        return True
