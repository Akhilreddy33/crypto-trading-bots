from dataclasses import dataclass, field
from typing import Callable, Any

import pandas as pd

from .collectors import fetch_klines
from .trader import calculate_stop_take


@dataclass
class BacktestTrade:
    symbol: str
    side: str
    entry_time: Any
    entry_price: float
    exit_time: Any
    exit_price: float
    pnl: float
    return_pct: float
    notes: str = ""


@dataclass
class BacktestReport:
    symbol: str
    strategy_name: str
    trades: list[BacktestTrade] = field(default_factory=list)
    total_return_pct: float = 0.0
    win_rate: float = 0.0
    average_return_pct: float = 0.0
    total_trades: int = 0


def run_backtest(
    symbol: str,
    signal_fn: Callable[[pd.DataFrame], tuple[str, dict]],
    strategy_name: str = "Strategy",
    interval: str = "15m",
    limit: int = 500,
    amount_usdt: float = 100,
) -> BacktestReport:
    df = fetch_klines(symbol, interval=interval, limit=limit)
    report = BacktestReport(symbol=symbol, strategy_name=strategy_name)
    position = None

    for i in range(40, len(df)):
        history = df.iloc[: i + 1].copy()
        side, summary = signal_fn(history)
        close_price = float(history["close"].iloc[-1])
        high_price = float(history["high"].iloc[-1])
        low_price = float(history["low"].iloc[-1])
        current_time = history["close_time"].iloc[-1]

        if position is None and side in {"BUY", "SELL"}:
            entry_price = close_price
            position = {
                "side": side,
                "entry_time": current_time,
                "entry_price": entry_price,
                "amount_usdt": amount_usdt,
                "stop_take": calculate_stop_take(entry_price, side),
                "notes": summary,
            }
            continue

        if position is not None:
            stop = position["stop_take"]["stop_loss"]
            take = position["stop_take"]["take_profit"]
            exit_price = None
            exit_reason = ""

            if position["side"] == "BUY":
                if low_price <= stop:
                    exit_price = stop
                    exit_reason = "stop_loss"
                elif high_price >= take:
                    exit_price = take
                    exit_reason = "take_profit"
                elif side == "SELL":
                    exit_price = close_price
                    exit_reason = "signal_reverse"
            else:
                if high_price >= stop:
                    exit_price = stop
                    exit_reason = "stop_loss"
                elif low_price <= take:
                    exit_price = take
                    exit_reason = "take_profit"
                elif side == "BUY":
                    exit_price = close_price
                    exit_reason = "signal_reverse"

            if exit_price is not None:
                entry_price = position["entry_price"]
                direction = 1 if position["side"] == "BUY" else -1
                quantity = amount_usdt / entry_price
                pnl = direction * (exit_price - entry_price) * quantity
                return_pct = (exit_price / entry_price - 1) * direction * 100
                report.trades.append(
                    BacktestTrade(
                        symbol=symbol,
                        side=position["side"],
                        entry_time=position["entry_time"],
                        entry_price=entry_price,
                        exit_time=current_time,
                        exit_price=exit_price,
                        pnl=round(pnl, 2),
                        return_pct=round(return_pct, 2),
                        notes=exit_reason,
                    )
                )
                position = None

    # Close any remaining open position at the last price
    if position is not None:
        final_price = float(df["close"].iloc[-1])
        final_time = df["close_time"].iloc[-1]
        entry_price = position["entry_price"]
        direction = 1 if position["side"] == "BUY" else -1
        quantity = amount_usdt / entry_price
        pnl = direction * (final_price - entry_price) * quantity
        return_pct = (final_price / entry_price - 1) * direction * 100
        report.trades.append(
            BacktestTrade(
                symbol=symbol,
                side=position["side"],
                entry_time=position["entry_time"],
                entry_price=entry_price,
                exit_time=final_time,
                exit_price=final_price,
                pnl=round(pnl, 2),
                return_pct=round(return_pct, 2),
                notes="end_of_data",
            )
        )

    report.total_trades = len(report.trades)
    if report.total_trades:
        total_return = sum(trade.return_pct for trade in report.trades)
        wins = sum(1 for trade in report.trades if trade.pnl > 0)
        report.total_return_pct = round(total_return, 2)
        report.average_return_pct = round(total_return / report.total_trades, 2)
        report.win_rate = round(wins / report.total_trades * 100, 2)
    return report
