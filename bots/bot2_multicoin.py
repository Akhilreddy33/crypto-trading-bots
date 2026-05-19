"""Bot 2: Multi-coin signal scanner."""

from shared.collectors import fetch_klines
from shared.indicators import ema, rsi, macd
from shared.ai_brain import confirm_signal, signal_summary
from shared.risk import max_trade_amount
from shared.trader import order_market, simulate_order
from shared.config import TRADE_SIZE, COIN_LIST

SYMBOLS = COIN_LIST[:10]


def score_coin(df):
    close = df["close"]
    df["ema_20"] = ema(close, 20)
    df["rsi"] = rsi(close, 14)
    macd_df = macd(close)
    df = df.join(macd_df)

    latest = df.iloc[-1]
    side = "HOLD"
    score = 0.0
    summary = {}

    if latest["rsi"] < 40 and latest["macd"] > latest["signal"]:
        side = "BUY"
        score = (40 - latest["rsi"]) + latest["histogram"] * 2
    elif latest["rsi"] > 60 and latest["macd"] < latest["signal"]:
        side = "SELL"
        score = (latest["rsi"] - 60) + abs(latest["histogram"]) * 2

    summary = {
        "rsi": float(latest["rsi"]),
        "macd": float(latest["macd"]),
        "signal": float(latest["signal"]),
        "histogram": float(latest["histogram"]),
        "close": float(latest["close"]),
        "ema_20": float(df["ema_20"].iloc[-1]),
    }
    return side, score, summary


def run_bot():
    print("Running Bot 2: scanning multiple coins...")
    candidates = []

    for symbol in SYMBOLS:
        df = fetch_klines(symbol, interval="15m", limit=100)
        side, score, summary = score_coin(df)
        print(f"{symbol}: {side} score={score:.1f}")
        if side != "HOLD" and score > 5:
            candidates.append((symbol, side, score, summary))

    if not candidates:
        print("No strong multi-coin signals found.")
        return

    symbol, side, score, summary = max(candidates, key=lambda item: item[2])
    summary_text = signal_summary(summary)
    confirmed = confirm_signal(symbol, side, summary_text)
    print(f"Selected {symbol} {side} with score {score:.1f}. AI confirmed: {confirmed}")
    if not confirmed:
        print("AI rejected the chosen signal.")
        return

    try:
        amount_usdt = max_trade_amount(TRADE_SIZE)
        order = order_market(symbol=symbol, side=side, amount_usdt=amount_usdt, filename="bot2_trades.log")
        print("Order placed:", order)
    except Exception as exc:
        print("Trade failed, simulating instead:", exc)
        quantity = float(TRADE_SIZE)
        order = simulate_order(symbol=symbol, side=side, quantity=quantity, filename="bot2_trades.log")
        print(order)


if __name__ == "__main__":
    run_bot()
