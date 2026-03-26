import logging
import pyupbit

logger = logging.getLogger(__name__)


class UpbitAPI:
    def __init__(self, access_key: str, secret_key: str):
        self.upbit = pyupbit.Upbit(access_key, secret_key)

    def get_krw_balance(self) -> float | None:
        try:
            balance = self.upbit.get_balance("KRW")
            return float(balance)
        except Exception as e:
            logger.error(f"Failed to get KRW balance: {e}")
            return None

    def get_balance(self, ticker: str) -> float | None:
        try:
            coin = ticker.split("-")[1] if "-" in ticker else ticker
            balance = self.upbit.get_balance(coin)
            return float(balance)
        except Exception as e:
            logger.error(f"Failed to get balance for {ticker}: {e}")
            return None

    def get_current_price(self, ticker: str) -> float | None:
        try:
            price = pyupbit.get_current_price(ticker)
            return float(price) if price else None
        except Exception as e:
            logger.error(f"Failed to get current price for {ticker}: {e}")
            return None

    def get_ohlcv(self, ticker: str, interval: str = "day", count: int = 20):
        try:
            df = pyupbit.get_ohlcv(ticker, interval=interval, count=count)
            return df
        except Exception as e:
            logger.error(f"Failed to get OHLCV for {ticker}: {e}")
            return None

    def buy_market(self, ticker: str, krw_amount: float) -> dict | None:
        try:
            result = self.upbit.buy_market_order(ticker, krw_amount)
            if isinstance(result, dict) and "error" in result:
                logger.error(f"Buy order error: {result}")
                return None
            logger.info(f"Buy order placed: {ticker} {krw_amount:,.0f} KRW -> {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to place buy order: {e}")
            return None

    def sell_market(self, ticker: str, volume: float) -> dict | None:
        try:
            result = self.upbit.sell_market_order(ticker, volume)
            if isinstance(result, dict) and "error" in result:
                logger.error(f"Sell order error: {result}")
                return None
            logger.info(f"Sell order placed: {ticker} {volume} -> {result}")
            return result
        except Exception as e:
            logger.error(f"Failed to place sell order: {e}")
            return None

    def get_avg_buy_price(self, ticker: str) -> float | None:
        try:
            balances = self.upbit.get_balances()
            coin = ticker.split("-")[1] if "-" in ticker else ticker
            for b in balances:
                if b["currency"] == coin:
                    return float(b["avg_buy_price"])
            return None
        except Exception as e:
            logger.error(f"Failed to get avg buy price: {e}")
            return None
