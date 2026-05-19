import os
import pandas as pd
from dotenv import load_dotenv

from .config import FETCH_INTERVAL

load_dotenv()

try:
    from binance.spot import Spot
except ImportError:
    Spot = None

BINANCE_TESTNET_API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
BINANCE_TESTNET_API_SECRET = os.getenv("BINANCE_TESTNET_API_SECRET")
BASE_URL_TESTNET = "https://testnet.binance.vision/api"


def get_binance_client(testnet: bool = True):
    if Spot is None:
        raise ImportError("binance.spot.Spot is required. Install binance-connector from requirements.txt")

    api_key = BINANCE_TESTNET_API_KEY
    api_secret = BINANCE_TESTNET_API_SECRET

    if not api_key or not api_secret:
        raise ValueError("Missing Binance Testnet API credentials in .env")

    if testnet:
        return Spot(api_key=api_key, api_secret=api_secret, base_url=BASE_URL_TESTNET)
    return Spot(api_key=api_key, api_secret=api_secret)


def fetch_klines(symbol: str, interval: str = FETCH_INTERVAL, limit: int = 200) -> pd.DataFrame:
    client = get_binance_client(testnet=True)
    if hasattr(client, "klines"):
        raw = client.klines(symbol=symbol, interval=interval, limit=limit)
    else:
        raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    df = pd.DataFrame(raw, columns=[
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_asset_volume",
        "number_of_trades",
        "taker_buy_base_asset_volume",
        "taker_buy_quote_asset_volume",
        "ignore",
    ])
    df = df.astype({
        "open": float,
        "high": float,
        "low": float,
        "close": float,
        "volume": float,
    })
    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms")
    return df


def fetch_price(symbol: str) -> float:
    df = fetch_klines(symbol, interval="1m", limit=2)
    return float(df["close"].iloc[-1])
