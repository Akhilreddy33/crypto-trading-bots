"""Technical indicators: RSI, MACD, EMA, Bollinger Bands, ATR, etc."""

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """MACD line, signal line, and histogram."""
    ema_fast = ema(series, fast)
    ema_slow = ema(series, slow)
    macd_line = ema_fast - ema_slow
    signal_line = ema(macd_line, signal)
    histogram = macd_line - signal_line
    return macd_line, signal_line, histogram


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    """Bollinger Bands: upper, middle, lower."""
    middle = sma(series, period)
    rolling_std = series.rolling(window=period).std()
    upper = middle + (rolling_std * std_dev)
    lower = middle - (rolling_std * std_dev)
    return upper, middle, lower


def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
    """Average True Range."""
    high = df["high"]
    low = df["low"]
    close = df["close"].shift(1)
    tr1 = high - low
    tr2 = (high - close).abs()
    tr3 = (low - close).abs()
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return true_range.rolling(window=period).mean()


def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3):
    """Stochastic oscillator %K and %D."""
    low_min = df["low"].rolling(window=k_period).min()
    high_max = df["high"].rolling(window=k_period).max()
    k = 100 * (df["close"] - low_min) / (high_max - low_min)
    d = k.rolling(window=d_period).mean()
    return k, d


def vwap(df: pd.DataFrame) -> pd.Series:
    """Volume Weighted Average Price."""
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    cumulative_tp_vol = (typical_price * df["volume"]).cumsum()
    cumulative_vol = df["volume"].cumsum()
    return cumulative_tp_vol / cumulative_vol


def obv(df: pd.DataFrame) -> pd.Series:
    """On-Balance Volume."""
    direction = np.sign(df["close"].diff())
    return (direction * df["volume"]).cumsum()


def support_resistance(df: pd.DataFrame, window: int = 20):
    """Simple support/resistance from rolling min/max."""
    support = df["low"].rolling(window=window).min().iloc[-1]
    resistance = df["high"].rolling(window=window).max().iloc[-1]
    return support, resistance


def compute_all(df: pd.DataFrame) -> pd.DataFrame:
    """Add all indicators to a DataFrame."""
    df = df.copy()
    close = df["close"]

    df["ema_9"] = ema(close, 9)
    df["ema_21"] = ema(close, 21)
    df["ema_50"] = ema(close, 50)
    df["sma_20"] = sma(close, 20)
    df["rsi"] = rsi(close)
    df["macd"], df["macd_signal"], df["macd_hist"] = macd(close)
    df["bb_upper"], df["bb_middle"], df["bb_lower"] = bollinger_bands(close)
    df["atr"] = atr(df)
    df["stoch_k"], df["stoch_d"] = stochastic(df)
    df["vwap"] = vwap(df)
    df["obv"] = obv(df)

    return df
