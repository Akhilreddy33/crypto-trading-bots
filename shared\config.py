import os
from dotenv import load_dotenv

load_dotenv()

TRADING_MODE = os.getenv("TRADING_MODE", "testnet").lower()
SIMULATION_MODE = os.getenv("SIMULATION_MODE", "true").lower() in ("1", "true", "yes")
TRADE_SIZE = float(os.getenv("TRADE_SIZE", 100))
MAX_RISK_PERCENT = float(os.getenv("MAX_RISK_PERCENT", 1.0))
STARTING_BALANCE = float(os.getenv("STARTING_BALANCE", 1000))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", 2.0))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", 3.0))
FETCH_INTERVAL = os.getenv("FETCH_INTERVAL", "15m")
COIN_LIST = [
    (symbol.strip().upper() + "USDT") if not symbol.strip().upper().endswith("USDT") else symbol.strip().upper()
    for symbol in os.getenv("COINS", "BTC,ETH,SOL,BNB,ADA,DOGE,MATIC,AVAX,DOT,LINK").split(",")
    if symbol.strip()
]

DEFAULT_SYMBOLS = COIN_LIST[:10]
