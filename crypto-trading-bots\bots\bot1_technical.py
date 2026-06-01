"""Bot 1: Technical Analysis Bot.

Uses RSI, MACD, and EMA crossovers to generate BUY/SELL signals on BTC and ETH.
"""

import os
from dotenv import load_dotenv

from shared.collectors import get_klines, get_price
from shared.indicators import compute_all
from shared.ai_brain import confirm_signal
from shared.trader import execute_trade

load_dotenv()

SYMBOLS = ["BTCUSDT", "ETHUSDT"]
INTERVAL = os.getenv("FETCH_INTERVAL", "15m")


def build_signal(df):
    """Generate a trading signal from indicator DataFrame.

    Returns (signal, metadata) where signal is BUY/SELL/HOLD.
    """
    if len(df) < 30:
        return "HOLD", {"reason": "Not enough data"}

    last = df.iloc[-1]
    prev = df.iloc[-2]

    reasons = []
    buy_score = 0
    sell_score = 0

    # RSI signals
    if last["rsi"] < 30:
        buy_score += 2
        reasons.append("RSI oversold")
    elif last["rsi"] > 70:
        sell_score += 2
        reasons.append("RSI overbought")

    # MACD crossover
    if last["macd"] > last["macd_signal"] and prev["macd"] <= prev["macd_signal"]:
        buy_score += 2
        reasons.append("MACD bullish crossover")
    elif last["macd"] < last["macd_signal"] and prev["macd"] >= prev["macd_signal"]:
        sell_score += 2
        reasons.append("MACD bearish crossover")

    # EMA crossover (9/21)
    if last["ema_9"] > last["ema_21"] and prev["ema_9"] <= prev["ema_21"]:
        buy_score += 1
        reasons.append("EMA 9/21 bullish cross")
    elif last["ema_9"] < last["ema_21"] and prev["ema_9"] >= prev["ema_21"]:
        sell_score += 1
        reasons.append("EMA 9/21 bearish cross")

    # Price vs EMA 50 trend
    if last["close"] > last["ema_50"]:
        buy_score += 1
        reasons.append("Above EMA 50")
    else:
        sell_score += 1
        reasons.append("Below EMA 50")

    # MACD histogram direction
    if last["macd_hist"] > 0 and last["macd_hist"] > prev["macd_hist"]:
        buy_score += 1
    elif last["macd_hist"] < 0 and last["macd_hist"] < prev["macd_hist"]:
        sell_score += 1

    if buy_score >= 4:
        return "BUY", {"reason": "; ".join(reasons), "score": buy_score}
    elif sell_score >= 4:
        return "SELL", {"reason": "; ".join(reasons), "score": sell_score}

    return "HOLD", {"reason": "; ".join(reasons) if reasons else "No strong signal"}


def run_bot():
    """Run Bot 1 on configured symbols."""
    print("Bot 1 Technical Analysis starting...")

    for symbol in SYMBOLS:
        print(f"  Analyzing {symbol}...")
        df = get_klines(symbol=symbol, interval=INTERVAL, limit=100)
        df = compute_all(df)

        signal, metadata = build_signal(df)
        print(f"  {symbol}: Signal={signal} | {metadata.get('reason', '')}")

        if signal == "HOLD":
            continue

        # Get AI confirmation
        last = df.iloc[-1]
        indicators = {
            "rsi": round(last["rsi"], 2),
            "macd": round(last["macd"], 4),
            "macd_signal": round(last["macd_signal"], 4),
            "ema_9": round(last["ema_9"], 2),
            "ema_21": round(last["ema_21"], 2),
            "ema_50": round(last["ema_50"], 2),
            "price": round(last["close"], 2),
        }

        ai_result = confirm_signal(
            symbol=symbol,
            signal=signal,
            indicators=indicators,
            strategy_name="Technical Analysis",
        )
        print(f"  AI: confirmed={ai_result['confirmed']}, confidence={ai_result['confidence']}")

        if ai_result["confirmed"] and ai_result["confidence"] >= 60:
            price = get_price(symbol)
            execute_trade(
                symbol=symbol,
                side=signal,
                bot_name="bot1_technical",
                price=price,
                reason=f"{metadata['reason']} | AI: {ai_result['reasoning']}",
            )
            print(f"  TRADE EXECUTED: {signal} {symbol} @ {price}")
        else:
            print(f"  AI rejected signal: {ai_result['reasoning']}")

    print("Bot 1 Technical Analysis complete.")
