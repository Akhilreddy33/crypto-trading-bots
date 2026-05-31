import os
from shared.collectors import fetch_klines
from shared.indicators import ema, rsi, macd
from shared.ai_brain import confirm_signal, signal_summary
from shared.risk import max_trade_amount
from shared.trader import order_market, simulate_order
from shared.config import TRADE_SIZE, COIN_LIST

SYMBOLS = COIN_LIST[:2]


def build_signal(df):
    close = df["close"]
    df["ema_20"] = ema(close, 20)
    df["ema_50"] = ema(close, 50)
    df["rsi"] = rsi(close, 14)
    macd_df = macd(close)
    df = df.join(macd_df)

    latest = df.iloc[-1]
    if latest["rsi"] < 35 and latest["macd"] > latest["signal"] and latest["close"] > latest["ema_20"]:
        return "BUY", {
            "rsi": float(latest["rsi"]),
            "macd": float(latest["macd"]),
            "signal": float(latest["signal"]),
            "ema_20": float(latest["ema_20"]),
            "ema_50": float(latest["ema_50"]),
        }
    if latest["rsi"] > 65 and latest["macd"] < latest["signal"] and latest["close"] < latest["ema_20"]:
        return "SELL", {
            "rsi": float(latest["rsi"]),
            "macd": float(latest["macd"]),
            "signal": float(latest["signal"]),
            "ema_20": float(latest["ema_20"]),
            "ema_50": float(latest["ema_50"]),
        }
    return "HOLD", {}


def run_bot():
    for symbol in SYMBOLS:
        print(f"Fetching market data for {symbol}...")
        df = fetch_klines(symbol, interval="15m", limit=100)
        signal, summary = build_signal(df)
        summary_text = signal_summary(summary)
        print(f"Signal for {symbol}: {signal}")
        if signal == "HOLD":
            continue

        confirmed = confirm_signal(symbol, signal, summary_text)
        print(f"AI confirmation: {confirmed}")
        if not confirmed:
            print("Signal not confirmed by AI, skipping trade.")
            continue

        try:
            amount_usdt = max_trade_amount(TRADE_SIZE)
            order = order_market(symbol=symbol, side=signal, amount_usdt=amount_usdt, filename="bot1_trades.log")
            print("Order placed:", order)
        except Exception as exc:
            print("Order failed, simulating instead:", exc)
            quantity = float(TRADE_SIZE)
            order = simulate_order(symbol=symbol, side=signal, quantity=quantity, filename="bot1_trades.log")
            print(order)


if __name__ == "__main__":
    run_bot()
