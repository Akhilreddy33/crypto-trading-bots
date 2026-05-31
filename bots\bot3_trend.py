"""Bot 3: Trend following bot."""

from shared.collectors import fetch_klines
from shared.indicators import ema, macd
from shared.ai_brain import confirm_signal, signal_summary
from shared.risk import max_trade_amount
from shared.trader import order_market, simulate_order
from shared.config import TRADE_SIZE, COIN_LIST

SYMBOLS = COIN_LIST[:5]


def build_signal(df):
    close = df["close"]
    df["ema_200"] = ema(close, 200)
    df["ema_50"] = ema(close, 50)
    macd_df = macd(close)
    df = df.join(macd_df)

    latest = df.iloc[-1]
    if latest["close"] > latest["ema_200"] and latest["macd"] > latest["signal"] and latest["close"] > latest["ema_50"]:
        return "BUY", {
            "close": float(latest["close"]),
            "ema_200": float(latest["ema_200"]),
            "ema_50": float(latest["ema_50"]),
            "macd": float(latest["macd"]),
            "signal": float(latest["signal"]),
        }
    if latest["close"] < latest["ema_200"] and latest["macd"] < latest["signal"] and latest["close"] < latest["ema_50"]:
        return "SELL", {
            "close": float(latest["close"]),
            "ema_200": float(latest["ema_200"]),
            "ema_50": float(latest["ema_50"]),
            "macd": float(latest["macd"]),
            "signal": float(latest["signal"]),
        }
    return "HOLD", {}


def run_bot():
    print("Running Bot 3: trend following...")
    for symbol in SYMBOLS:
        df = fetch_klines(symbol, interval="15m", limit=150)
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
            order = order_market(symbol=symbol, side=side, amount_usdt=amount_usdt, filename="bot3_trend.log")
            print("Order placed:", order)
        except Exception as exc:
            print("Trade failed, simulating instead:", exc)
            quantity = float(TRADE_SIZE)
            order = simulate_order(symbol=symbol, side=side, quantity=quantity, filename="bot3_trend.log")
            print(order)


if __name__ == "__main__":
    run_bot()
