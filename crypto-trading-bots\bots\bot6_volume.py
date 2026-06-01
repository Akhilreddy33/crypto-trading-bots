"""Bot 6: Volume Spike Bot.

Detects unusual volume spikes across top coins and trades in the direction of the spike.
"""

import os
from dotenv import load_dotenv

from shared.collectors import get_klines, get_price, get_top_coins
from shared.indicators import compute_all
from shared.ai_brain import confirm_signal
from shared.trader import execute_trade

load_dotenv()

TOP_N = int(os.getenv("TOP_COINS_SCAN", "20"))
INTERVAL = os.getenv("FETCH_INTERVAL", "15m")
VOLUME_THRESHOLD = 2.5  # Must be 2.5x average volume
MAX_TRADES_PER_RUN = 3


def _detect_volume_spike(df):
    """Detect volume spikes and determine direction.

    Returns (signal, metadata) or ("HOLD", metadata).
    """
    if len(df) < 30:
        return "HOLD", {"reason": "Insufficient data"}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    avg_volume = df["volume"].iloc[-20:-1].mean()
    if avg_volume == 0:
        return "HOLD", {"reason": "No volume data"}

    vol_ratio = last["volume"] / avg_volume
    reasons = []

    if vol_ratio < VOLUME_THRESHOLD:
        return "HOLD", {"reason": f"Volume ratio {vol_ratio:.1f}x (need {VOLUME_THRESHOLD}x)"}

    reasons.append(f"Volume spike: {vol_ratio:.1f}x average")

    # Determine direction from price action on the spike candle
    candle_body = last["close"] - last["open"]
    candle_range = last["high"] - last["low"]

    if candle_range == 0:
        return "HOLD", {"reason": "No price movement on volume spike"}

    body_pct = abs(candle_body) / candle_range

    buy_score = 0
    sell_score = 0

    # Strong bullish candle on volume
    if candle_body > 0 and body_pct > 0.6:
        buy_score += 3
        reasons.append(f"Strong bullish candle ({body_pct:.0%} body)")
    elif candle_body < 0 and body_pct > 0.6:
        sell_score += 3
        reasons.append(f"Strong bearish candle ({body_pct:.0%} body)")

    # OBV confirmation
    if len(df) > 5:
        obv_change = last["obv"] - df.iloc[-5]["obv"]
        if obv_change > 0 and buy_score > 0:
            buy_score += 1
            reasons.append("OBV rising")
        elif obv_change < 0 and sell_score > 0:
            sell_score += 1
            reasons.append("OBV falling")

    # Trend alignment
    if last["close"] > last["ema_21"] and buy_score > 0:
        buy_score += 1
        reasons.append("Price above EMA21")
    elif last["close"] < last["ema_21"] and sell_score > 0:
        sell_score += 1
        reasons.append("Price below EMA21")

    # RSI not at extremes (avoid chasing)
    if last["rsi"] > 75:
        buy_score -= 1
        reasons.append("RSI too high, risky buy")
    elif last["rsi"] < 25:
        sell_score -= 1
        reasons.append("RSI too low, risky sell")

    if buy_score >= 3:
        return "BUY", {"reason": "; ".join(reasons), "vol_ratio": vol_ratio}
    elif sell_score >= 3:
        return "SELL", {"reason": "; ".join(reasons), "vol_ratio": vol_ratio}

    return "HOLD", {"reason": f"Volume spike but unclear direction ({vol_ratio:.1f}x)"}


def run_bot():
    """Run Bot 6 Volume Spike detection."""
    print("Bot 6 Volume Spike starting...")

    try:
        symbols = get_top_coins(limit=TOP_N)
    except Exception:
        coins_env = os.getenv("COINS", "BTC,ETH,SOL,BNB,ADA,DOGE,MATIC,AVAX,DOT,LINK")
        symbols = [c.strip() + "USDT" for c in coins_env.split(",")]

    print(f"  Scanning {len(symbols)} coins for volume spikes...")
    spikes = []

    for symbol in symbols:
        try:
            df = get_klines(symbol=symbol, interval=INTERVAL, limit=50)
            df = compute_all(df)
            signal, metadata = _detect_volume_spike(df)
            if signal != "HOLD":
                spikes.append((symbol, signal, metadata, df))
                print(f"  SPIKE: {symbol} {signal} | {metadata['reason']}")
        except Exception as exc:
            continue  # Skip coins that error

    # Sort by volume ratio and take top trades
    spikes.sort(key=lambda x: x[2].get("vol_ratio", 0), reverse=True)

    trades_made = 0
    for symbol, signal, metadata, df in spikes[:MAX_TRADES_PER_RUN]:
        last = df.iloc[-1]
        indicators = {
            "rsi": round(last["rsi"], 2),
            "volume_ratio": metadata.get("vol_ratio", 0),
            "ema_21": round(last["ema_21"], 2),
            "obv_trend": "up" if last["obv"] > df.iloc[-5]["obv"] else "down",
            "price": round(last["close"], 2),
        }

        ai_result = confirm_signal(
            symbol=symbol,
            signal=signal,
            indicators=indicators,
            strategy_name="Volume Spike",
        )

        if ai_result["confirmed"] and ai_result["confidence"] >= 55:
            price = get_price(symbol)
            execute_trade(
                symbol=symbol,
                side=signal,
                bot_name="bot6_volume",
                price=price,
                reason=f"{metadata['reason']} | AI: {ai_result['reasoning']}",
            )
            trades_made += 1
            print(f"  TRADE: {signal} {symbol} @ {price}")

    print(f"Bot 6 complete. {trades_made} trades from {len(spikes)} spikes detected.")
