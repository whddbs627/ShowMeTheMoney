"""전략 로직 테스트"""
import pandas as pd
import numpy as np
import pytest
from strategy import (
    calc_target_price, check_ma_filter, calc_rsi,
    should_buy_volatility, should_buy_rsi_bounce,
    should_buy_golden_cross, should_buy_combined, should_buy,
)


def make_ohlcv(closes, highs=None, lows=None, opens=None):
    n = len(closes)
    if highs is None:
        highs = [c * 1.02 for c in closes]
    if lows is None:
        lows = [c * 0.98 for c in closes]
    if opens is None:
        opens = closes[:]
    dates = pd.date_range("2024-01-01", periods=n)
    return pd.DataFrame({
        "open": opens, "high": highs, "low": lows,
        "close": closes, "volume": [1000] * n,
    }, index=dates)


class TestCalcTargetPrice:
    def test_basic(self):
        df = make_ohlcv(
            closes=[100, 110],
            highs=[120, 115],
            lows=[90, 105],
            opens=[95, 108],
        )
        # target = today_open + (yesterday_high - yesterday_low) * 0.5
        # = 108 + (120 - 90) * 0.5 = 108 + 15 = 123
        assert calc_target_price(df, 0.5) == 123.0

    def test_k_zero(self):
        df = make_ohlcv(closes=[100, 110], opens=[95, 108])
        # k=0 → target = today_open
        assert calc_target_price(df, 0.0) == 108.0

    def test_k_one(self):
        df = make_ohlcv(
            closes=[100, 110],
            highs=[120, 115],
            lows=[80, 105],
            opens=[95, 108],
        )
        # target = 108 + (120 - 80) * 1.0 = 148
        assert calc_target_price(df, 1.0) == 148.0


class TestCheckMAFilter:
    def test_uptrend(self):
        closes = list(range(80, 101))
        df = make_ohlcv(closes)
        assert bool(check_ma_filter(df)) is True

    def test_downtrend(self):
        closes = list(range(100, 79, -1))
        df = make_ohlcv(closes)
        assert bool(check_ma_filter(df)) is False


class TestCalcRSI:
    def test_overbought(self):
        # 계속 상승 → RSI 높음
        closes = [100 + i * 2 for i in range(21)]
        df = make_ohlcv(closes)
        assert calc_rsi(df) > 70

    def test_oversold(self):
        # 계속 하락 → RSI 낮음
        closes = [200 - i * 2 for i in range(21)]
        df = make_ohlcv(closes)
        assert calc_rsi(df) < 30

    def test_range(self):
        closes = [100 + (i % 5) for i in range(21)]
        df = make_ohlcv(closes)
        rsi = calc_rsi(df)
        assert 0 <= rsi <= 100


class TestShouldBuyVolatility:
    def test_buy_signal(self):
        df_short = make_ohlcv(
            closes=[100, 110], highs=[120, 115], lows=[90, 105], opens=[95, 100],
        )
        df_long = make_ohlcv(list(range(80, 101)))
        # target = 100 + (120-90)*0.5 = 115
        # price=120 > 115 → buy
        assert should_buy_volatility(df_short, df_long, 120, 0.5, False, False, 30) is True

    def test_no_signal_below_target(self):
        df_short = make_ohlcv(
            closes=[100, 110], highs=[120, 115], lows=[90, 105], opens=[95, 100],
        )
        df_long = make_ohlcv(list(range(80, 101)))
        # target = 115, price = 110 < 115
        assert should_buy_volatility(df_short, df_long, 110, 0.5, False, False, 30) is False

    def test_ma_filter_blocks(self):
        df_short = make_ohlcv(
            closes=[100, 110], highs=[120, 115], lows=[90, 105], opens=[95, 100],
        )
        df_long = make_ohlcv(list(range(100, 79, -1)))  # 하락추세
        assert should_buy_volatility(df_short, df_long, 120, 0.5, True, False, 30) is False


class TestShouldBuy:
    def test_strategy_selection(self):
        df_short = make_ohlcv(
            closes=[100, 110], highs=[120, 115], lows=[90, 105], opens=[95, 100],
        )
        df_long = make_ohlcv(list(range(80, 101)))

        # volatility_breakout
        result = should_buy(df_short, df_long, 120, 0.5, False, False, 30, "volatility_breakout")
        assert result is True

        # unknown strategy falls back to volatility_breakout
        result = should_buy(df_short, df_long, 120, 0.5, False, False, 30, "unknown_strategy")
        assert result is True
