"""Bot 6: Volume spike bot."""

from shared.collectors import fetch_klines
from shared.ai_brain import confirm_signal, signal_summary
from shared.risk import max_trade_amount
from shared.trader import order_market, simulate_order
from shared.config import TRADE_SIZE, COIN_LIST

SYMBOLS = COIN_LIST[:10]


def build_signal(df):
    latest = df.iloc[-1]
    average_volume = df["volume"].iloc[-21:-1].mean()
    previous = df.iloc[-2]

    if latest["volume"] > average_volume * 3:
        if latest["close"] > previous["close"] * 1.003:
            return "BUY", {
                "volume": float(latest["volume"]),
                "avg_volume": float(average_volume),
                "close": float(latest["close"]),
            }
        if latest["close"] < previous["close"] * 0.997:
            return "SELL", {
                "volume": float(latest["volume"]),
                "avg_volume": float(average_volume),
                "close": float(latest["close"]),
            }
    return "HOLD", {}


def run_bot():
    print("Running Bot 6: volume spike scanner...")
    for symbol in SYMBOLS:
        df = fetch_klines(symbol, interval="15m", limit=80)
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
            order = order_market(symbol=symbol, side=side, amount_usdt=amount_usdt, filename="bot6_volume.log")
            print("Order placed:", order)
        except Exception as exc:
            print("Trade failed, simulating instead:", exc)
            quantity = float(TRADE_SIZE)
            order = simulate_order(symbol=symbol, side=side, quantity=quantity, filename="bot6_volume.log")
            print(order)


if __name__ == "__main__":
    run_bot()
