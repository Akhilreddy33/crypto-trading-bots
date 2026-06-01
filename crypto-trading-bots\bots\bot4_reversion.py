"""Bot 4: Mean Reversion Bot.

Trades when price deviates significantly from the mean, expecting a reversion.
Uses Bollinger Bands and RSI to detect oversold/overbought extremes.
"""

import os
from dotenv import load_dotenv

from shared.collectors import get_klines, get_price
from shared.indicators import compute_all
from shared.ai_brain import confirm_signal
from shared.trader import execute_trade

load_dotenv()

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT"]
INTERVAL = os.getenv("FETCH_INTERVAL", "15m")


def build_signal(df):
    """Mean reversion signal: buy oversold, sell overbought.

    Returns (signal, metadata).
    """
    if len(df) < 30:
        return "HOLD", {"reason": "Insufficient data"}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    reasons = []
    buy_score = 0
    sell_score = 0

    # Bollinger Band position
    bb_range = last["bb_upper"] - last["bb_lower"]
    if bb_range > 0:
        bb_pct = (last["close"] - last["bb_lower"]) / bb_range
    else:
        bb_pct = 0.5

    if bb_pct < 0.05:
        buy_score += 3
        reasons.append(f"Price at BB lower (BB%={bb_pct:.2f})")
    elif bb_pct < 0.2:
        buy_score += 2
        reasons.append(f"Price near BB lower (BB%={bb_pct:.2f})")
    elif bb_pct > 0.95:
        sell_score += 3
        reasons.append(f"Price at BB upper (BB%={bb_pct:.2f})")
    elif bb_pct > 0.8:
        sell_score += 2
        reasons.append(f"Price near BB upper (BB%={bb_pct:.2f})")

    # RSI extremes (stronger thresholds for mean reversion)
    if last["rsi"] < 25:
        buy_score += 3
        reasons.append(f"RSI extremely oversold ({last['rsi']:.1f})")
    elif last["rsi"] < 35:
        buy_score += 2
        reasons.append(f"RSI oversold ({last['rsi']:.1f})")
    elif last["rsi"] > 75:
        sell_score += 3
        reasons.append(f"RSI extremely overbought ({last['rsi']:.1f})")
    elif last["rsi"] > 65:
        sell_score += 2
        reasons.append(f"RSI overbought ({last['rsi']:.1f})")

    # Stochastic confirmation
    if last["stoch_k"] < 20 and last["stoch_d"] < 20:
        buy_score += 1
        reasons.append("Stochastic oversold")
    elif last["stoch_k"] > 80 and last["stoch_d"] > 80:
        sell_score += 1
        reasons.append("Stochastic overbought")

    # Price distance from SMA 20 (mean)
    deviation = (last["close"] - last["sma_20"]) / last["sma_20"] * 100
    if deviation < -3:
        buy_score += 1
        reasons.append(f"Price {deviation:.1f}% below SMA20")
    elif deviation > 3:
        sell_score += 1
        reasons.append(f"Price {deviation:.1f}% above SMA20")

    # Reversal candle patterns
    if last["close"] > last["open"] and prev["close"] < prev["open"]:
        if last["low"] < prev["low"]:
            buy_score += 1
            reasons.append("Bullish engulfing pattern")
    elif last["close"] < last["open"] and prev["close"] > prev["open"]:
        if last["high"] > prev["high"]:
            sell_score += 1
            reasons.append("Bearish engulfing pattern")

    if buy_score >= 4:
        return "BUY", {"reason": "; ".join(reasons)}
    elif sell_score >= 4:
        return "SELL", {"reason": "; ".join(reasons)}

    return "HOLD", {"reason": "; ".join(reasons) if reasons else "No extremes detected"}


def run_bot():
    """Run Bot 4 Mean Reversion."""
    print("Bot 4 Mean Reversion starting...")

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
            "bb_pct": round((last["close"] - last["bb_lower"]) / (last["bb_upper"] - last["bb_lower"]), 2) if last["bb_upper"] != last["bb_lower"] else 0.5,
            "stoch_k": round(last["stoch_k"], 2),
            "sma_20": round(last["sma_20"], 2),
            "price": round(last["close"], 2),
        }

        ai_result = confirm_signal(
            symbol=symbol,
            signal=signal,
            indicators=indicators,
            strategy_name="Mean Reversion",
        )

        if ai_result["confirmed"] and ai_result["confidence"] >= 60:
            price = get_price(symbol)
            execute_trade(
                symbol=symbol,
                side=signal,
                bot_name="bot4_reversion",
                price=price,
                reason=f"{metadata['reason']} | AI: {ai_result['reasoning']}",
            )
            print(f"  TRADE: {signal} {symbol} @ {price}")
        else:
            print(f"  AI rejected: {ai_result['reasoning']}")

    print("Bot 4 Mean Reversion complete.")
