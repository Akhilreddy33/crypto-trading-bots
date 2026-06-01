"""Bot 3: Trend Following Bot.

Only trades in the direction of the prevailing trend using EMA alignment and ADX-like logic.
"""

import os
from dotenv import load_dotenv

from shared.collectors import get_klines, get_price
from shared.indicators import compute_all, ema
from shared.ai_brain import confirm_signal
from shared.trader import execute_trade

load_dotenv()

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
INTERVAL = os.getenv("FETCH_INTERVAL", "15m")


def build_signal(df):
    """Trend following signal: only buy in confirmed uptrends.

    Returns (signal, metadata).
    """
    if len(df) < 50:
        return "HOLD", {"reason": "Insufficient data for trend analysis"}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    reasons = []
    trend_strength = 0

    # EMA alignment check (9 > 21 > 50 = uptrend)
    if last["ema_9"] > last["ema_21"] > last["ema_50"]:
        trend_strength += 3
        reasons.append("EMA aligned bullish (9>21>50)")
    elif last["ema_9"] < last["ema_21"] < last["ema_50"]:
        trend_strength -= 3
        reasons.append("EMA aligned bearish (9<21<50)")

    # Price making higher highs/lows (last 10 candles)
    recent = df.iloc[-10:]
    if recent["high"].iloc[-1] > recent["high"].iloc[:-1].max():
        trend_strength += 1
        reasons.append("New local high")
    if recent["low"].iloc[-1] < recent["low"].iloc[:-1].min():
        trend_strength -= 1
        reasons.append("New local low")

    # EMA 9 slope (momentum)
    ema9_slope = (last["ema_9"] - df.iloc[-5]["ema_9"]) / df.iloc[-5]["ema_9"] * 100
    if ema9_slope > 0.3:
        trend_strength += 1
        reasons.append(f"EMA9 slope up ({ema9_slope:.2f}%)")
    elif ema9_slope < -0.3:
        trend_strength -= 1
        reasons.append(f"EMA9 slope down ({ema9_slope:.2f}%)")

    # Price above VWAP
    if last["close"] > last["vwap"]:
        trend_strength += 1
        reasons.append("Above VWAP")
    else:
        trend_strength -= 1
        reasons.append("Below VWAP")

    # Pullback entry: price dips to EMA 21 in uptrend
    if trend_strength >= 3 and last["low"] <= last["ema_21"] * 1.005:
        trend_strength += 1
        reasons.append("Pullback to EMA21 in uptrend")

    # Exit: EMA crossover down
    if last["ema_9"] < last["ema_21"] and prev["ema_9"] >= prev["ema_21"]:
        return "SELL", {"reason": "EMA 9 crossed below 21 - trend exit"}

    if trend_strength >= 4:
        return "BUY", {"reason": "; ".join(reasons)}
    elif trend_strength <= -3:
        return "SELL", {"reason": "; ".join(reasons)}

    return "HOLD", {"reason": "; ".join(reasons) if reasons else "No clear trend"}


def run_bot():
    """Run Bot 3 Trend Following."""
    print("Bot 3 Trend Following starting...")

    for symbol in SYMBOLS:
        print(f"  Analyzing {symbol}...")
        df = get_klines(symbol=symbol, interval=INTERVAL, limit=100)
        df = compute_all(df)

        signal, metadata = build_signal(df)
        print(f"  {symbol}: Signal={signal} | {metadata.get('reason', '')}")

        if signal == "HOLD":
            continue

        last = df.iloc[-1]
        indicators = {
            "rsi": round(last["rsi"], 2),
            "ema_9": round(last["ema_9"], 2),
            "ema_21": round(last["ema_21"], 2),
            "ema_50": round(last["ema_50"], 2),
            "vwap": round(last["vwap"], 2),
            "price": round(last["close"], 2),
        }

        ai_result = confirm_signal(
            symbol=symbol,
            signal=signal,
            indicators=indicators,
            strategy_name="Trend Following",
        )

        if ai_result["confirmed"] and ai_result["confidence"] >= 60:
            price = get_price(symbol)
            execute_trade(
                symbol=symbol,
                side=signal,
                bot_name="bot3_trend",
                price=price,
                reason=f"{metadata['reason']} | AI: {ai_result['reasoning']}",
            )
            print(f"  TRADE: {signal} {symbol} @ {price}")
        else:
            print(f"  AI rejected: {ai_result['reasoning']}")

    print("Bot 3 Trend Following complete.")
