import os
import pandas as pd
import requests
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
PUBLIC_BINANCE_API = "https://api.binance.com/api/v3/klines"
PUBLIC_BINANCE_US_API = "https://api.binance.us/api/v3/klines"
PUBLIC_TESTNET_API = "https://testnet.binance.vision/api/v3/klines"


def _has_valid_api_credentials(key: str, secret: str) -> bool:
    if not key or not secret:
        return False
    if key.startswith("your_") or secret.startswith("your_"):
        return False
    if "api" in key.lower() and "key" in key.lower() and "secret" in secret.lower():
        return False
    return True


def get_binance_client(testnet: bool = True):
    if Spot is None:
        raise ImportError("binance.spot.Spot is required. Install binance-connector from requirements.txt")

    api_key = BINANCE_TESTNET_API_KEY
    api_secret = BINANCE_TESTNET_API_SECRET

    if not _has_valid_api_credentials(api_key, api_secret):
        raise ValueError("Missing or invalid Binance Testnet API credentials in .env")

    if testnet:
        return Spot(api_key=api_key, api_secret=api_secret, base_url=BASE_URL_TESTNET)
    return Spot(api_key=api_key, api_secret=api_secret)


def fetch_klines(symbol: str, interval: str = FETCH_INTERVAL, limit: int = 200) -> pd.DataFrame:
    if _has_valid_api_credentials(BINANCE_TESTNET_API_KEY, BINANCE_TESTNET_API_SECRET):
        client = get_binance_client(testnet=True)
        if hasattr(client, "klines"):
            raw = client.klines(symbol=symbol, interval=interval, limit=limit)
        else:
            raw = client.get_klines(symbol=symbol, interval=interval, limit=limit)
    else:
        raw = fetch_public_klines(symbol=symbol, interval=interval, limit=limit)

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


def fetch_public_klines(symbol: str, interval: str = FETCH_INTERVAL, limit: int = 200):
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    headers = {"User-Agent": "Mozilla/5.0"}
    for url in [PUBLIC_BINANCE_API, PUBLIC_BINANCE_US_API, PUBLIC_TESTNET_API]:
        try:
            response = requests.get(url, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            continue

    raise RuntimeError(
        "Unable to fetch historical price data from Binance public APIs. "
        "Check your internet access or use a valid Binance Testnet API key."
    )


def fetch_price(symbol: str) -> float:
    df = fetch_klines(symbol, interval="1m", limit=2)
    return float(df["close"].iloc[-1])
