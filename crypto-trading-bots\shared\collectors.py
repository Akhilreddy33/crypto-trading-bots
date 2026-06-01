"""Data collectors for fetching price data from Binance."""

import os
from typing import Optional

import pandas as pd
from binance.spot import Spot
from dotenv import load_dotenv

load_dotenv()

TRADING_MODE = os.getenv("TRADING_MODE", "testnet")
BINANCE_TESTNET_BASE = "https://testnet.binance.vision"


def _get_client() -> Spot:
    if TRADING_MODE == "live":
        return Spot(
            api_key=os.getenv("BINANCE_REAL_API_KEY"),
            api_secret=os.getenv("BINANCE_REAL_API_SECRET"),
        )
    return Spot(
        api_key=os.getenv("BINANCE_TESTNET_API_KEY"),
        api_secret=os.getenv("BINANCE_TESTNET_API_SECRET"),
        base_url=BINANCE_TESTNET_BASE,
    )


def get_klines(
    symbol: str = "BTCUSDT",
    interval: str = "15m",
    limit: int = 100,
) -> pd.DataFrame:
    """Fetch kline/candlestick data and return as a DataFrame."""
    client = _get_client()
    raw = client.klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(
        raw,
        columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore",
        ],
    )
    for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
        df[col] = df[col].astype(float)
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    return df


def get_price(symbol: str = "BTCUSDT") -> float:
    """Get current price for a symbol."""
    client = _get_client()
    ticker = client.ticker_price(symbol=symbol)
    return float(ticker["price"])


def get_24h_stats(symbol: str = "BTCUSDT") -> dict:
    """Get 24-hour statistics for a symbol."""
    client = _get_client()
    stats = client.ticker_24hr(symbol=symbol)
    return {
        "price": float(stats["lastPrice"]),
        "change_pct": float(stats["priceChangePercent"]),
        "high": float(stats["highPrice"]),
        "low": float(stats["lowPrice"]),
        "volume": float(stats["volume"]),
        "quote_volume": float(stats["quoteVolume"]),
        "trades": int(stats["count"]),
    }


def get_top_coins(limit: int = 10) -> list[str]:
    """Return top coins by 24h quote volume."""
    client = _get_client()
    tickers = client.ticker_24hr()
    usdt_pairs = [t for t in tickers if t["symbol"].endswith("USDT")]
    usdt_pairs.sort(key=lambda t: float(t["quoteVolume"]), reverse=True)
    return [t["symbol"] for t in usdt_pairs[:limit]]


def get_order_book(symbol: str = "BTCUSDT", limit: int = 20) -> dict:
    """Get order book for support/resistance detection."""
    client = _get_client()
    book = client.depth(symbol=symbol, limit=limit)
    bids = [(float(p), float(q)) for p, q in book["bids"]]
    asks = [(float(p), float(q)) for p, q in book["asks"]]
    return {"bids": bids, "asks": asks}
