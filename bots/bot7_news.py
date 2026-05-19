"""Bot 7: News sentiment trading bot."""

from shared.ai_brain import analyze_news_sentiment
from shared.news import fetch_reddit_news
from shared.risk import max_trade_amount
from shared.trader import order_market, simulate_order
from shared.config import TRADE_SIZE, COIN_LIST


def detect_symbol_from_text(text: str) -> str:
    text_lower = text.lower()
    for symbol in COIN_LIST:
        coin = symbol.replace("USDT", "").lower()
        if coin in text_lower:
            return symbol
    return "BTCUSDT"


def run_bot():
    print("Running Bot 7: news sentiment analysis...")
    news_items = fetch_reddit_news(limit=8)
    if not news_items:
        print("No news available, skipping Bot 7.")
        return

    for item in news_items:
        title = item.get("title", "")
        body = item.get("selftext", "") or ""
        symbol = detect_symbol_from_text(title + " " + body)
        sentiment = analyze_news_sentiment(title, body)
        print(f"News: {title[:80]}...")
        print(f"Detected symbol: {symbol}, sentiment: {sentiment}")

        if sentiment == "NEUTRAL":
            continue

        side = "BUY" if sentiment == "BULLISH" else "SELL"
        try:
            amount_usdt = max_trade_amount(TRADE_SIZE)
            order = order_market(symbol=symbol, side=side, amount_usdt=amount_usdt, filename="bot7_news.log")
            print("Order placed:", order)
            return
        except Exception as exc:
            print("Trade failed, simulating instead:", exc)
            quantity = float(TRADE_SIZE)
            order = simulate_order(symbol=symbol, side=side, quantity=quantity, filename="bot7_news.log")
            print(order)
            return

    print("No strong news-driven trade found.")


if __name__ == "__main__":
    run_bot()
