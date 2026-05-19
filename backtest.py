import sys
from typing import Callable

from bots.bot1_technical import build_signal as bot1_signal
from bots.bot3_trend import build_signal as bot3_signal
from bots.bot4_reversion import build_signal as bot4_signal
from shared.backtester import run_backtest


STRATEGIES = {
    "bot1": (bot1_signal, "Bot 1 Technical Analysis"),
    "bot3": (bot3_signal, "Bot 3 Trend Following"),
    "bot4": (bot4_signal, "Bot 4 Mean Reversion"),
}


def print_report(report):
    print(f"Backtest: {report.strategy_name} on {report.symbol}")
    print(f"Trades: {report.total_trades}")
    print(f"Total return (%): {report.total_return_pct}")
    print(f"Average return (%): {report.average_return_pct}")
    print(f"Win rate: {report.win_rate}%")
    print("Recent trades:")
    for trade in report.trades[-5:]:
        print(
            f"  {trade.side} {trade.entry_time} -> {trade.exit_time} | "
            f"entry {trade.entry_price}, exit {trade.exit_price}, "
            f"pnl {trade.pnl}, return {trade.return_pct}%, reason {trade.notes}"
        )


def strategy_wrapper(signal_fn: Callable, history):
    result = signal_fn(history)
    if isinstance(result, tuple) and len(result) >= 2:
        return result[0], result[1]
    return result, {}


def main():
    symbol = "BTCUSDT"
    strategy_key = "bot1"
    if len(sys.argv) >= 2:
        strategy_key = sys.argv[1]
    if len(sys.argv) >= 3:
        symbol = sys.argv[2]

    if strategy_key not in STRATEGIES:
        print(f"Unknown strategy: {strategy_key}")
        print("Available strategies: " + ", ".join(STRATEGIES.keys()))
        return

    signal_fn, strategy_name = STRATEGIES[strategy_key]
    wrapped = lambda history: strategy_wrapper(signal_fn, history)
    report = run_backtest(symbol=symbol, signal_fn=wrapped, strategy_name=strategy_name, amount_usdt=100)
    print_report(report)


if __name__ == "__main__":
    main()
