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


# === 전략 1: 변동성 돌파 ===
def should_buy_volatility(df_short, df_long, current_price, k, use_ma, use_rsi, rsi_lower):
    """현재가 > 당일시가 + 전일변동폭×K 이면 매수"""
    target = calc_target_price(df_short, k)
    if current_price < target:
        return False
    if use_ma and not check_ma_filter(df_long):
        return False
    if use_rsi and calc_rsi(df_long) < rsi_lower:
        return False
    return True


# === 전략 2: RSI 반등 ===
def should_buy_rsi_bounce(df_short, df_long, current_price, k, use_ma, use_rsi, rsi_lower):
    """RSI가 과매도 구간에서 반등할 때 매수"""
    rsi = calc_rsi(df_long)
    close = df_long["close"]
    prev_rsi = calc_rsi(df_long.iloc[:-1]) if len(df_long) > 15 else rsi

    # RSI가 하한 아래에서 위로 돌파
    if prev_rsi < rsi_lower and rsi >= rsi_lower:
        if use_ma and not check_ma_filter(df_long):
            return False
        return True
    return False


# === 전략 3: 골든크로스 (이동평균 교차) ===
def should_buy_golden_cross(df_short, df_long, current_price, k, use_ma, use_rsi, rsi_lower):
    """5일선이 20일선을 상향 돌파할 때 매수"""
    close = df_long["close"]
    ma5 = close.rolling(window=5).mean()
    ma20 = close.rolling(window=20).mean()

    if len(ma5) < 2 or len(ma20) < 2:
        return False

    # 어제: 5MA < 20MA, 오늘: 5MA > 20MA → 골든크로스
    prev_cross = ma5.iloc[-2] < ma20.iloc[-2]
    curr_cross = ma5.iloc[-1] > ma20.iloc[-1]

    if prev_cross and curr_cross:
        if use_rsi and calc_rsi(df_long) < rsi_lower:
            return False
        return True
    return False


# === 전략 4: 복합 (변동성 돌파 + RSI + MA 모두 충족) ===
def should_buy_combined(df_short, df_long, current_price, k, use_ma, use_rsi, rsi_lower):
    """변동성 돌파 + 상승추세 + RSI 양호 모두 충족"""
    target = calc_target_price(df_short, k)
    if current_price < target:
        return False
    if not check_ma_filter(df_long):
        return False
    rsi = calc_rsi(df_long)
    if rsi < rsi_lower or rsi > 70:
        return False
    return True


# 전략 매핑
STRATEGIES = {
    "volatility_breakout": should_buy_volatility,
    "rsi_bounce": should_buy_rsi_bounce,
    "golden_cross": should_buy_golden_cross,
    "combined": should_buy_combined,
}

# 이전 버전 호환
def should_buy(df_short, df_long, current_price, k, use_ma=True, use_rsi=True, rsi_lower=30.0, strategy_type="volatility_breakout"):
    fn = STRATEGIES.get(strategy_type, should_buy_volatility)
    return fn(df_short, df_long, current_price, k, use_ma, use_rsi, rsi_lower)
