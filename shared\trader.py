import os
import json
from datetime import datetime
from dotenv import load_dotenv

from .collectors import fetch_price
from .config import SIMULATION_MODE, STOP_LOSS_PCT, TAKE_PROFIT_PCT

load_dotenv()

try:
    from binance.spot import Spot
except ImportError:
    Spot = None

BINANCE_TESTNET_API_KEY = os.getenv("BINANCE_TESTNET_API_KEY")
BINANCE_TESTNET_API_SECRET = os.getenv("BINANCE_TESTNET_API_SECRET")
TRADING_MODE = os.getenv("TRADING_MODE", "testnet").lower()
LOG_PATH = os.path.join(os.path.dirname(__file__), "..", "logs")
BASE_URL_TESTNET = "https://testnet.binance.vision/api"


def _get_binance_client():
    if Spot is None:
        raise ImportError("binance.spot.Spot is required. Install dependencies from requirements.txt")
    if TRADING_MODE != "testnet":
        raise ValueError("Only testnet trading mode is supported by this starter code")
    return Spot(api_key=BINANCE_TESTNET_API_KEY, api_secret=BINANCE_TESTNET_API_SECRET, base_url=BASE_URL_TESTNET)


def log_trade(message: str, filename: str = "bot1_trades.log"):
    path = os.path.join(LOG_PATH, filename)
    os.makedirs(LOG_PATH, exist_ok=True)
    now = datetime.utcnow().isoformat()
    line = f"{now} | {message}\n"
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(line)


def get_trade_quantity(symbol: str, amount_usdt: float) -> float:
    price = fetch_price(symbol)
    if price <= 0:
        raise ValueError(f"Unable to get price for {symbol}")
    quantity = round(amount_usdt / price, 6)
    return max(quantity, 0.000001)


def place_order(symbol: str, side: str, quantity: float, filename: str = "bot1_trades.log"):
    if SIMULATION_MODE:
        return simulate_order(symbol, side, quantity, filename=filename)
    if TRADING_MODE != "testnet":
        raise ValueError("Only testnet order placement is enabled by this starter project")

    client = _get_binance_client()
    order = client.new_order(symbol=symbol, side=side.upper(), type="MARKET", quantity=str(quantity))
    log_trade(json.dumps({
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "order": order,
    }), filename=filename)
    return order


def calculate_stop_take(price: float, side: str, stop_loss_pct: float = STOP_LOSS_PCT, take_profit_pct: float = TAKE_PROFIT_PCT) -> dict:
    if side.upper() == "BUY":
        return {
            "stop_loss": round(price * (1 - stop_loss_pct / 100), 6),
            "take_profit": round(price * (1 + take_profit_pct / 100), 6),
        }
    return {
        "stop_loss": round(price * (1 + stop_loss_pct / 100), 6),
        "take_profit": round(price * (1 - take_profit_pct / 100), 6),
    }


def order_market(symbol: str, side: str, amount_usdt: float, filename: str = "bot1_trades.log"):
    quantity = get_trade_quantity(symbol, amount_usdt)
    if quantity <= 0:
        raise ValueError("Trade quantity calculated as zero.")
    return place_order(symbol, side, quantity, filename=filename)


def simulate_order(symbol: str, side: str, quantity: float, filename: str = "bot1_trades.log"):
    price = fetch_price(symbol)
    levels = calculate_stop_take(price, side)
    log_trade(json.dumps({
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "status": "SIMULATED",
        "stop_loss": levels["stop_loss"],
        "take_profit": levels["take_profit"],
    }), filename=filename)
    return {
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "status": "SIMULATED",
        "stop_loss": levels["stop_loss"],
        "take_profit": levels["take_profit"],
    }
