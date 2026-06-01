"""Bot 5: Breakout Trading Bot.

Detects breakouts above resistance or below support using price action and volume.
"""

import os
from dotenv import load_dotenv

from shared.collectors import get_klines, get_price
from shared.indicators import compute_all, support_resistance
from shared.ai_brain import confirm_signal
from shared.trader import execute_trade

load_dotenv()

SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "ADAUSDT"]
INTERVAL = os.getenv("FETCH_INTERVAL", "15m")


def _detect_breakout(df):
    """Detect breakout signals based on support/resistance and volume.

    Returns (signal, metadata).
    """
    if len(df) < 30:
        return "HOLD", {"reason": "Insufficient data"}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    # Calculate support and resistance from recent history
    lookback = df.iloc[-20:]
    support = lookback["low"].min()
    resistance = lookback["high"].max()

    # Narrow range detection (consolidation)
    price_range = resistance - support
    avg_price = (resistance + support) / 2
    range_pct = (price_range / avg_price) * 100

    reasons = []
    buy_score = 0
    sell_score = 0

    # Breakout above resistance
    if last["close"] > resistance and prev["close"] <= resistance:
        buy_score += 3
        reasons.append(f"Breakout above resistance ({resistance:.2f})")
    # Breakdown below support
    elif last["close"] < support and prev["close"] >= support:
        sell_score += 3
        reasons.append(f"Breakdown below support ({support:.2f})")

    # Volume confirmation (breakout needs volume)
    avg_vol = df["volume"].iloc[-20:].mean()
    vol_ratio = last["volume"] / avg_vol if avg_vol > 0 else 1

    if vol_ratio > 2.0:
        if buy_score > 0:
            buy_score += 2
        elif sell_score > 0:
            sell_score += 2
        reasons.append(f"Volume {vol_ratio:.1f}x average")
    elif vol_ratio > 1.5:
        if buy_score > 0:
            buy_score += 1
        elif sell_score > 0:
            sell_score += 1
        reasons.append(f"Volume {vol_ratio:.1f}x average")

    # ATR expansion (volatility breakout)
    if len(df) > 5:
        current_atr = last["atr"]
        prev_atr = df.iloc[-5]["atr"]
        if current_atr > prev_atr * 1.3:
            if buy_score > 0:
                buy_score += 1
            elif sell_score > 0:
                sell_score += 1
            reasons.append("ATR expanding (volatility breakout)")

    # Consolidation prior to breakout (tight range)
    if range_pct < 3.0:
        if buy_score > 0:
            buy_score += 1
        elif sell_score > 0:
            sell_score += 1
        reasons.append(f"Tight consolidation ({range_pct:.1f}% range)")

    # MACD momentum alignment
    if last["macd_hist"] > 0 and buy_score > 0:
        buy_score += 1
        reasons.append("MACD positive")
    elif last["macd_hist"] < 0 and sell_score > 0:
        sell_score += 1
        reasons.append("MACD negative")

    if buy_score >= 4:
        return "BUY", {"reason": "; ".join(reasons), "resistance": resistance, "support": support}
    elif sell_score >= 4:
        return "SELL", {"reason": "; ".join(reasons), "resistance": resistance, "support": support}

    return "HOLD", {"reason": "; ".join(reasons) if reasons else "No breakout detected"}


def run_bot():
    """Run Bot 5 Breakout Trading."""
    print("Bot 5 Breakout Trading starting...")

    for symbol in SYMBOLS:
        print(f"  Analyzing {symbol}...")
        df = get_klines(symbol=symbol, interval=INTERVAL, limit=100)
        df = compute_all(df)

        signal, metadata = _detect_breakout(df)
        print(f"  {symbol}: Signal={signal} | {metadata.get('reason', '')}")

        if signal == "HOLD":
            continue

        last = df.iloc[-1]
        indicators = {
            "rsi": round(last["rsi"], 2),
            "atr": round(last["atr"], 4),
            "volume_vs_avg": round(last["volume"] / df["volume"].iloc[-20:].mean(), 2),
            "macd_hist": round(last["macd_hist"], 4),
            "resistance": metadata.get("resistance"),
            "support": metadata.get("support"),
            "price": round(last["close"], 2),
        }

        ai_result = confirm_signal(
            symbol=symbol,
            signal=signal,
            indicators=indicators,
            strategy_name="Breakout Trading",
        )

        if ai_result["confirmed"] and ai_result["confidence"] >= 60:
            price = get_price(symbol)
            execute_trade(
                symbol=symbol,
                side=signal,
                bot_name="bot5_breakout",
                price=price,
                reason=f"{metadata['reason']} | AI: {ai_result['reasoning']}",
            )
            print(f"  TRADE: {signal} {symbol} @ {price}")
        else:
            print(f"  AI rejected: {ai_result['reasoning']}")

    print("Bot 5 Breakout Trading complete.")
