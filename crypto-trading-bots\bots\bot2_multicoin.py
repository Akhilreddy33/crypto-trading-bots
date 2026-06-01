"""Bot 2: Multi-Coin Scanner.

Scans top coins by volume and picks the best trading signals.
"""

import os
from dotenv import load_dotenv

from shared.collectors import get_klines, get_price, get_top_coins
from shared.indicators import compute_all
from shared.ai_brain import confirm_signal
from shared.trader import execute_trade

load_dotenv()

COINS_ENV = os.getenv("COINS", "BTC,ETH,SOL,BNB,ADA,DOGE,MATIC,AVAX,DOT,LINK")
COIN_LIST = [c.strip() + "USDT" for c in COINS_ENV.split(",")]
INTERVAL = os.getenv("FETCH_INTERVAL", "15m")
MAX_TRADES_PER_RUN = 3


def _score_coin(df) -> tuple:
    """Score a coin based on combined indicator strength. Returns (score, signal, reason)."""
    if len(df) < 30:
        return 0, "HOLD", "Insufficient data"

    last = df.iloc[-1]
    prev = df.iloc[-2]
    score = 0
    reasons = []

    # RSI extremes
    if last["rsi"] < 35:
        score += 2
        reasons.append(f"RSI={last['rsi']:.1f} oversold")
    elif last["rsi"] > 65:
        score -= 2
        reasons.append(f"RSI={last['rsi']:.1f} overbought")

    # MACD momentum
    if last["macd_hist"] > 0 and last["macd_hist"] > prev["macd_hist"]:
        score += 2
        reasons.append("MACD momentum up")
    elif last["macd_hist"] < 0 and last["macd_hist"] < prev["macd_hist"]:
        score -= 2
        reasons.append("MACD momentum down")

    # EMA trend
    if last["ema_9"] > last["ema_21"] > last["ema_50"]:
        score += 2
        reasons.append("Strong uptrend (EMA aligned)")
    elif last["ema_9"] < last["ema_21"] < last["ema_50"]:
        score -= 2
        reasons.append("Strong downtrend")

    # Bollinger band position
    bb_pct = (last["close"] - last["bb_lower"]) / (last["bb_upper"] - last["bb_lower"]) if last["bb_upper"] != last["bb_lower"] else 0.5
    if bb_pct < 0.2:
        score += 1
        reasons.append("Near BB lower")
    elif bb_pct > 0.8:
        score -= 1
        reasons.append("Near BB upper")

    # Volume surge
    avg_vol = df["volume"].iloc[-20:].mean()
    if last["volume"] > avg_vol * 1.5:
        score += 1
        reasons.append("Volume surge")

    if score >= 4:
        return score, "BUY", "; ".join(reasons)
    elif score <= -4:
        return abs(score), "SELL", "; ".join(reasons)
    return abs(score), "HOLD", "; ".join(reasons) if reasons else "No signal"


def run_bot():
    """Run Bot 2 Multi-Coin Scanner."""
    print("Bot 2 Multi-Coin Scanner starting...")

    candidates = []

    for symbol in COIN_LIST:
        try:
            df = get_klines(symbol=symbol, interval=INTERVAL, limit=100)
            df = compute_all(df)
            score, signal, reason = _score_coin(df)
            if signal != "HOLD":
                candidates.append((score, symbol, signal, reason, df))
                print(f"  {symbol}: score={score} signal={signal} | {reason}")
        except Exception as exc:
            print(f"  {symbol}: Error - {exc}")

    # Sort by score and take top signals
    candidates.sort(key=lambda x: x[0], reverse=True)

    trades_made = 0
    for score, symbol, signal, reason, df in candidates[:MAX_TRADES_PER_RUN]:
        last = df.iloc[-1]
        indicators = {
            "rsi": round(last["rsi"], 2),
            "macd_hist": round(last["macd_hist"], 4),
            "ema_9": round(last["ema_9"], 2),
            "ema_21": round(last["ema_21"], 2),
            "score": score,
        }

        ai_result = confirm_signal(
            symbol=symbol,
            signal=signal,
            indicators=indicators,
            strategy_name="Multi-Coin Scanner",
        )

        if ai_result["confirmed"] and ai_result["confidence"] >= 55:
            price = get_price(symbol)
            execute_trade(
                symbol=symbol,
                side=signal,
                bot_name="bot2_multicoin",
                price=price,
                reason=f"Score:{score} | {reason} | AI: {ai_result['reasoning']}",
            )
            trades_made += 1
            print(f"  TRADE: {signal} {symbol} @ {price}")

    print(f"Bot 2 complete. {trades_made} trades from {len(candidates)} candidates.")
