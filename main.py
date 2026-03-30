import time
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import config
from upbit_api import UpbitAPI
from strategy import should_buy
from trader import Trader
from notifier import Notifier


def setup_logging():
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(
        log_dir / "trading.log",
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.LOG_LEVEL))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def main():
    setup_logging()
    logger = logging.getLogger(__name__)

    logger.info("=== ShowMeTheMoney Bot Starting ===")
    logger.info(f"Ticker: {config.TICKER}, K: {config.K}")
    logger.info(f"Max Investment: {config.MAX_INVESTMENT_KRW:,.0f} KRW")
    logger.info(f"MA Filter: {config.USE_MA_FILTER}, RSI Filter: {config.USE_RSI_FILTER}")

    if not config.UPBIT_ACCESS_KEY or not config.UPBIT_SECRET_KEY:
        logger.error("UPBIT_ACCESS_KEY and UPBIT_SECRET_KEY must be set in .env")
        return

    api = UpbitAPI(config.UPBIT_ACCESS_KEY, config.UPBIT_SECRET_KEY)
    notifier = Notifier(config.DISCORD_WEBHOOK_URL)
    trader = Trader(
        api=api,
        notifier=notifier,
        ticker=config.TICKER,
        investment_ratio=config.INVESTMENT_RATIO,
        max_investment_krw=config.MAX_INVESTMENT_KRW,
        max_loss_pct=config.MAX_LOSS_PCT,
    )

    trader.sync_position()
    notifier.send(f"[START] Bot started - {config.TICKER}")

    while True:
        try:
            df_short = api.get_ohlcv(config.TICKER, "day", 2)
            df_long = api.get_ohlcv(config.TICKER, "day", 21)
            current_price = api.get_current_price(config.TICKER)

            if df_short is None or df_long is None or current_price is None:
                logger.warning("Failed to fetch market data, skipping...")
                time.sleep(config.CHECK_INTERVAL_SEC)
                continue

            if trader.holding:
                trader.check_and_sell(current_price)
            else:
                buy_signal = should_buy(
                    df_short=df_short,
                    df_long=df_long,
                    current_price=current_price,
                    k=config.K,
                    use_ma=config.USE_MA_FILTER,
                    use_rsi=config.USE_RSI_FILTER,
                    rsi_lower=config.RSI_LOWER_BOUND,
                )

                if buy_signal:
                    logger.info(f"Buy signal detected at {current_price:,.0f} KRW")

                trader.check_and_buy(current_price, buy_signal)

            time.sleep(config.CHECK_INTERVAL_SEC)

        except KeyboardInterrupt:
            logger.info("Shutting down...")
            notifier.send("[STOP] Bot stopped")
            break
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            notifier.send(f"[ERROR] {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()
