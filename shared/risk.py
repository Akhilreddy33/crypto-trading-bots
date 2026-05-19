from .config import MAX_RISK_PERCENT, STARTING_BALANCE


def risk_quantity(price: float) -> float:
    if price <= 0:
        raise ValueError("Price must be positive to calculate risk quantity.")
    amount = STARTING_BALANCE * MAX_RISK_PERCENT / 100.0
    quantity = round(amount / price, 6)
    return max(quantity, 0.000001)


def max_trade_amount(amount_usdt: float) -> float:
    risk_amount = STARTING_BALANCE * MAX_RISK_PERCENT / 100.0
    return min(amount_usdt, risk_amount)
