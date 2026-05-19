"""Bot 5: Breakout trading bot."""

from shared.collectors import fetch_klines
from shared.indicators import ema
from shared.ai_brain import confirm_signal, signal_summary
from shared.risk import max_trade_amount
from shared.trader import order_market, simulate_order
from shared.config import TRADE_SIZE, COIN_LIST

SYMBOLS = COIN_LIST[:5]


def build_signal(df):
    close = df["close"]
    df["ema_20"] = ema(close, 20)
    df["avg_volume"] = df["volume"].rolling(20).mean()

    latest = df.iloc[-1]
    previous = df.iloc[-2]
    resistance = df["high"].iloc[-25:-1].max()
    support = df["low"].iloc[-25:-1].min()

    if latest["close"] > resistance and latest["volume"] > latest["avg_volume"] * 2 and latest["close"] > previous["close"]:
        return "BUY", {
            "close": float(latest["close"]),
            "resistance": float(resistance),
            "volume": float(latest["volume"]),
            "avg_volume": float(latest["avg_volume"]),
        }
    if latest["close"] < support and latest["volume"] > latest["avg_volume"] * 2 and latest["close"] < previous["close"]:
        return "SELL", {
            "close": float(latest["close"]),
            "support": float(support),
            "volume": float(latest["volume"]),
            "avg_volume": float(latest["avg_volume"]),
        }
    return "HOLD", {}


def run_bot():
    print("Running Bot 5: breakout detection...")
    for symbol in SYMBOLS:
        df = fetch_klines(symbol, interval="15m", limit=120)
        side, summary = build_signal(df)
        print(f"{symbol}: {side}")
        if side == "HOLD":
            continue

        summary_text = signal_summary(summary)
        confirmed = confirm_signal(symbol, side, summary_text)
        print(f"AI confirmed: {confirmed}")
        if not confirmed:
            continue

        try:
            amount_usdt = max_trade_amount(TRADE_SIZE)
            order = order_market(symbol=symbol, side=side, amount_usdt=amount_usdt, filename="bot5_breakout.log")
            print("Order placed:", order)
        except Exception as exc:
            print("Trade failed, simulating instead:", exc)
            quantity = float(TRADE_SIZE)
            order = simulate_order(symbol=symbol, side=side, quantity=quantity, filename="bot5_breakout.log")
            print(order)


if __name__ == "__main__":
    run_bot()
