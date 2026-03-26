import logging
from datetime import datetime, timezone, timedelta

from upbit_api import UpbitAPI
from notifier import Notifier

logger = logging.getLogger(__name__)

KST = timezone(timedelta(hours=9))
# 업비트 일봉 리셋 시간: 09:00 KST
DAILY_RESET_HOUR = 9


class Trader:
    def __init__(
        self,
        api: UpbitAPI,
        notifier: Notifier,
        ticker: str,
        investment_ratio: float,
        max_investment_krw: float,
        max_loss_pct: float,
        take_profit_pct: float = 0.0,
    ):
        self.api = api
        self.notifier = notifier
        self.ticker = ticker
        self.investment_ratio = investment_ratio
        self.max_investment_krw = max_investment_krw
        self.max_loss_pct = max_loss_pct
        self.take_profit_pct = take_profit_pct  # 0이면 비활성

        self.holding = False
        self.buy_price = 0.0
        self.buy_date = None  # KST date when bought (일봉 기준일)
        self.bought_today = False  # 당일 매수 여부 (중복 매수 방지)
        self._last_reset_date = None  # 마지막 리셋 날짜

    def _get_trading_date(self) -> datetime.date:
        """업비트 일봉 기준 거래일 (09:00 KST 기준)"""
        now = datetime.now(KST)
        if now.hour < DAILY_RESET_HOUR:
            return (now - timedelta(days=1)).date()
        return now.date()

    def _check_daily_reset(self):
        """일봉 리셋 시 당일 매수 플래그 초기화"""
        today = self._get_trading_date()
        if self._last_reset_date != today:
            self._last_reset_date = today
            if not self.holding:
                self.bought_today = False

    def sync_position(self):
        """재시작 시 기존 보유 포지션 확인 (크래시 복구)"""
        balance = self.api.get_balance(self.ticker)
        if balance and balance > 0:
            avg_price = self.api.get_avg_buy_price(self.ticker)
            current_price = self.api.get_current_price(self.ticker)

            if avg_price and current_price and balance * current_price > 5000:
                self.holding = True
                self.buy_price = avg_price
                self.buy_date = self._get_trading_date()
                self.bought_today = True
                logger.info(
                    f"Synced position: {self.ticker} "
                    f"balance={balance:.8f}, avg_price={avg_price:,.0f}"
                )
                return

        self.holding = False
        logger.info(f"No position: {self.ticker}")

    def check_and_buy(self, current_price: float, should_buy: bool) -> bool:
        """매수 조건 확인 및 주문 실행"""
        self._check_daily_reset()

        if self.holding:
            return False

        if self.bought_today:
            return False

        if not should_buy:
            return False

        krw_balance = self.api.get_krw_balance()
        if krw_balance is None:
            return False

        amount = min(krw_balance * self.investment_ratio, self.max_investment_krw)

        if amount < 5000:
            logger.warning(f"Insufficient KRW: {amount:,.0f} for {self.ticker}")
            return False

        result = self.api.buy_market(self.ticker, amount)
        if result is None:
            return False

        self.holding = True
        self.buy_price = current_price
        self.buy_date = self._get_trading_date()
        self.bought_today = True

        msg = (
            f"[매수] {self.ticker}\n"
            f"가격: {current_price:,.0f}원\n"
            f"금액: {amount:,.0f}원"
        )
        self.notifier.send(msg)
        return True

    def check_and_sell(self, current_price: float) -> bool:
        """매도 조건 확인 및 주문 실행"""
        if not self.holding:
            return False

        self._check_daily_reset()

        trading_date = self._get_trading_date()

        # 익일 매도: 매수한 거래일과 현재 거래일이 다르면 매도
        # (09:00 KST 이후에만 "다음날"로 판정)
        is_new_day = self.buy_date and trading_date > self.buy_date

        # 손절: 매수가 대비 loss_pct 이상 하락
        is_stop_loss = current_price < self.buy_price * (1 - self.max_loss_pct)

        # 익절: 매수가 대비 take_profit_pct 이상 상승
        is_take_profit = (
            self.take_profit_pct > 0
            and current_price > self.buy_price * (1 + self.take_profit_pct)
        )

        reason = None
        if is_take_profit:
            reason = "TAKE_PROFIT"
        elif is_new_day:
            reason = "NEXT_DAY"
        elif is_stop_loss:
            reason = "STOP_LOSS"
        else:
            return False

        balance = self.api.get_balance(self.ticker)
        if not balance or balance <= 0:
            logger.warning(f"No balance to sell: {self.ticker}")
            self.holding = False
            return False

        result = self.api.sell_market(self.ticker, balance)
        if result is None:
            return False

        pnl_pct = ((current_price - self.buy_price) / self.buy_price) * 100
        self.holding = False
        self.bought_today = True  # 매도 후 당일 재매수 방지

        reason_kr = {"NEXT_DAY": "익일매도", "STOP_LOSS": "손절", "TAKE_PROFIT": "익절"}.get(reason, reason)
        msg = (
            f"[매도 - {reason_kr}] {self.ticker}\n"
            f"매수: {self.buy_price:,.0f} → 매도: {current_price:,.0f}원\n"
            f"수익률: {pnl_pct:+.2f}%"
        )
        self.notifier.send(msg)
        self.buy_price = 0.0
        self.buy_date = None
        return True
