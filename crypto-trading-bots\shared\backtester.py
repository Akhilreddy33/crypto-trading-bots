"""Backtesting engine for evaluating strategies on historical data."""

from dataclasses import dataclass, field
from typing import Callable

import pandas as pd

from shared.collectors import get_klines
from shared.indicators import compute_all


@dataclass
class Trade:
    side: str
    entry_time: str
    exit_time: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    return_pct: float
    notes: str = ""


@dataclass
class BacktestReport:
    strategy_name: str
    symbol: str
    total_trades: int
    total_return_pct: float
    average_return_pct: float
    win_rate: float
    trades: list = field(default_factory=list)


def run_backtest(
    symbol: str = "BTCUSDT",
    signal_fn: Callable = None,
    strategy_name: str = "Strategy",
    amount_usdt: float = 100,
    interval: str = "1h",
    limit: int = 500,
) -> BacktestReport:
    """Run a backtest on historical data.

    Args:
        symbol: Trading pair
        signal_fn: Function that takes a DataFrame slice and returns (signal, metadata)
                   signal should be "BUY", "SELL", or "HOLD"
        strategy_name: Name for the report
        amount_usdt: Amount per trade in USDT
        interval: Candle interval
        limit: Number of candles to fetch

    Returns:
        BacktestReport with trade results
    """
    df = get_klines(symbol=symbol, interval=interval, limit=limit)
    df = compute_all(df)
    df = df.dropna().reset_index(drop=True)

    trades: list[Trade] = []
    position = None  # None or dict with entry info
    lookback = 30  # minimum candles for indicators

    for i in range(lookback, len(df)):
        history = df.iloc[: i + 1].copy()
        current = df.iloc[i]

        signal, metadata = signal_fn(history)

        if position is None and signal == "BUY":
            position = {
                "entry_price": current["close"],
                "entry_time": str(current["open_time"]),
                "quantity": amount_usdt / current["close"],
                "reason": metadata.get("reason", ""),
            }
        elif position is not None and signal == "SELL":
            exit_price = current["close"]
            entry_price = position["entry_price"]
            pnl = (exit_price - entry_price) * position["quantity"]
            return_pct = round(((exit_price / entry_price) - 1) * 100, 2)

            trades.append(
                Trade(
                    side="BUY",
                    entry_time=position["entry_time"],
                    exit_time=str(current["open_time"]),
                    entry_price=round(entry_price, 2),
                    exit_price=round(exit_price, 2),
                    quantity=round(position["quantity"], 6),
                    pnl=round(pnl, 2),
                    return_pct=return_pct,
                    notes=position["reason"],
                )
            )
            position = None

    # Close any open position at end
    if position is not None:
        last = df.iloc[-1]
        exit_price = last["close"]
        entry_price = position["entry_price"]
        pnl = (exit_price - entry_price) * position["quantity"]
        return_pct = round(((exit_price / entry_price) - 1) * 100, 2)
        trades.append(
            Trade(
                side="BUY",
                entry_time=position["entry_time"],
                exit_time=str(last["open_time"]),
                entry_price=round(entry_price, 2),
                exit_price=round(exit_price, 2),
                quantity=round(position["quantity"], 6),
                pnl=round(pnl, 2),
                return_pct=return_pct,
                notes="closed at end of backtest",
            )
        )

    total_trades = len(trades)
    total_return = sum(t.return_pct for t in trades)
    avg_return = round(total_return / total_trades, 2) if total_trades > 0 else 0.0
    wins = sum(1 for t in trades if t.pnl > 0)
    win_rate = round((wins / total_trades) * 100, 1) if total_trades > 0 else 0.0

    return BacktestReport(
        strategy_name=strategy_name,
        symbol=symbol,
        total_trades=total_trades,
        total_return_pct=round(total_return, 2),
        average_return_pct=avg_return,
        win_rate=win_rate,
        trades=trades,
    )
