"""Trade execution module for Binance (testnet and live)."""

import os
import json
import logging
from datetime import datetime, timezone

from binance.spot import Spot
from dotenv import load_dotenv

load_dotenv()

TRADING_MODE = os.getenv("TRADING_MODE", "testnet")
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "true").lower() == "true"
TRADE_SIZE = float(os.getenv("TRADE_SIZE", "100"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "2.0"))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "3.0"))

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
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


def _get_logger(bot_name: str) -> logging.Logger:
    os.makedirs(LOG_DIR, exist_ok=True)
    logger = logging.getLogger(f"trader.{bot_name}")
    if not logger.handlers:
        handler = logging.FileHandler(
            os.path.join(LOG_DIR, f"{bot_name}_trades.log"), encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def execute_trade(
    symbol: str,
    side: str,
    bot_name: str,
    price: float,
    reason: str = "",
    amount_usdt: float = None,
) -> dict:
    """Execute a trade (or simulate it).

    Args:
        symbol: Trading pair (e.g. BTCUSDT)
        side: BUY or SELL
        bot_name: Name for logging (e.g. bot1_technical)
        price: Current price of the asset
        reason: Why this trade was triggered
        amount_usdt: USDT amount to trade (defaults to TRADE_SIZE env var)

    Returns:
        dict with trade details and status
    """
    if amount_usdt is None:
        amount_usdt = TRADE_SIZE

    quantity = round(amount_usdt / price, 6)
    logger = _get_logger(bot_name)

    trade_record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "symbol": symbol,
        "side": side,
        "price": price,
        "quantity": quantity,
        "amount_usdt": amount_usdt,
        "reason": reason,
        "mode": "SIMULATION" if SIMULATION_MODE else TRADING_MODE,
        "stop_loss": round(price * (1 - STOP_LOSS_PCT / 100), 2) if side == "BUY" else round(price * (1 + STOP_LOSS_PCT / 100), 2),
        "take_profit": round(price * (1 + TAKE_PROFIT_PCT / 100), 2) if side == "BUY" else round(price * (1 - TAKE_PROFIT_PCT / 100), 2),
    }

    if SIMULATION_MODE:
        trade_record["status"] = "SIMULATED"
        trade_record["order_id"] = None
    else:
        try:
            client = _get_client()
            order = client.new_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quoteOrderQty=str(amount_usdt),
            )
            trade_record["status"] = "EXECUTED"
            trade_record["order_id"] = order.get("orderId")
            trade_record["fills"] = order.get("fills", [])
        except Exception as exc:
            trade_record["status"] = "FAILED"
            trade_record["error"] = str(exc)

    logger.info(json.dumps(trade_record))
    return trade_record


def get_balance(asset: str = "USDT") -> float:
    """Get available balance for an asset."""
    if SIMULATION_MODE:
        return float(os.getenv("STARTING_BALANCE", "1000"))
    client = _get_client()
    account = client.account()
    for bal in account["balances"]:
        if bal["asset"] == asset:
            return float(bal["free"])
    return 0.0
