import pandas as pd


def calc_target_price(df: pd.DataFrame, k: float) -> float:
    """전일 변동폭 × K를 당일 시가에 더한 목표가 계산"""
    yesterday = df.iloc[-2]
    today_open = df.iloc[-1]["open"]
    target = today_open + (yesterday["high"] - yesterday["low"]) * k
    return target


def check_ma_filter(df: pd.DataFrame) -> bool:
    """5일 이동평균 > 20일 이동평균이면 True (상승추세)"""
    close = df["close"]
    ma5 = close.rolling(window=5).mean().iloc[-1]
    ma20 = close.rolling(window=20).mean().iloc[-1]
    return ma5 > ma20


def calc_rsi(df: pd.DataFrame, period: int = 14) -> float:
    """RSI 계산 (Wilder's smoothing)"""
    close = df["close"]
    delta = close.diff()

    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean().iloc[-1]

    if avg_loss == 0:
        return 100.0

    rs = avg_gain / avg_loss
    return 100.0 - (100.0 / (1.0 + rs))


def should_buy(
    df_short: pd.DataFrame,
    df_long: pd.DataFrame,
    current_price: float,
    k: float,
    use_ma: bool = True,
    use_rsi: bool = True,
    rsi_lower: float = 30.0,
) -> bool:
    """매수 조건 종합 판단"""
    target_price = calc_target_price(df_short, k)

    if current_price < target_price:
        return False

    if use_ma and not check_ma_filter(df_long):
        return False

    if use_rsi and calc_rsi(df_long) < rsi_lower:
        return False

    return True
