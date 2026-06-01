"""Bot 7: News Sentiment Bot.

Fetches crypto news from Reddit and uses AI to determine trading sentiment.
"""

import os
from dotenv import load_dotenv

from shared.collectors import get_price
from shared.ai_brain import analyze_sentiment, confirm_signal
from shared.trader import execute_trade

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET", "")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "CryptoBot/1.0")

SUBREDDITS = ["cryptocurrency", "bitcoin", "ethtrader", "CryptoMarkets"]
COIN_KEYWORDS = {
    "BTCUSDT": ["bitcoin", "btc", "₿"],
    "ETHUSDT": ["ethereum", "eth", "ether"],
    "SOLUSDT": ["solana", "sol"],
    "BNBUSDT": ["bnb", "binance coin"],
    "ADAUSDT": ["cardano", "ada"],
    "DOGEUSDT": ["dogecoin", "doge"],
}
MIN_SENTIMENT_SCORE = 40  # Minimum absolute sentiment to trade
MAX_TRADES_PER_RUN = 2


def _get_reddit_posts(limit: int = 25) -> list[dict]:
    """Fetch recent posts from crypto subreddits."""
    try:
        import praw
    except ImportError:
        print("  praw not installed. Skipping Reddit fetch.")
        return []

    if not REDDIT_CLIENT_ID or REDDIT_CLIENT_ID.startswith("your_"):
        print("  Reddit API not configured. Skipping.")
        return []

    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
    )

    posts = []
    for sub_name in SUBREDDITS:
        try:
            subreddit = reddit.subreddit(sub_name)
            for post in subreddit.hot(limit=limit):
                posts.append({
                    "title": post.title,
                    "score": post.score,
                    "subreddit": sub_name,
                    "url": post.url,
                    "created_utc": post.created_utc,
                })
        except Exception:
            continue

    return posts


def _match_coin(text: str) -> list[str]:
    """Match text to trading symbols based on keywords."""
    text_lower = text.lower()
    matched = []
    for symbol, keywords in COIN_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            matched.append(symbol)
    return matched


def run_bot():
    """Run Bot 7 News Sentiment analysis."""
    print("Bot 7 News Sentiment starting...")

    posts = _get_reddit_posts(limit=20)

    if not posts:
        print("  No posts retrieved. Check Reddit API configuration.")
        return

    print(f"  Fetched {len(posts)} posts. Analyzing sentiment...")

    # Aggregate sentiment per coin
    coin_sentiments: dict[str, list[int]] = {sym: [] for sym in COIN_KEYWORDS}

    for post in posts:
        matched_coins = _match_coin(post["title"])
        if not matched_coins:
            continue

        sentiment = analyze_sentiment(post["title"])

        for symbol in matched_coins:
            coin_sentiments[symbol].append(sentiment["score"])

    # Determine trading signals from aggregated sentiment
    candidates = []
    for symbol, scores in coin_sentiments.items():
        if not scores:
            continue

        avg_score = sum(scores) / len(scores)
        count = len(scores)

        if abs(avg_score) >= MIN_SENTIMENT_SCORE and count >= 2:
            signal = "BUY" if avg_score > 0 else "SELL"
            candidates.append((abs(avg_score), symbol, signal, avg_score, count))
            print(f"  {symbol}: sentiment={avg_score:.0f} mentions={count} -> {signal}")

    # Sort by sentiment strength
    candidates.sort(key=lambda x: x[0], reverse=True)

    trades_made = 0
    for _, symbol, signal, avg_score, count in candidates[:MAX_TRADES_PER_RUN]:
        indicators = {
            "sentiment_score": round(avg_score, 1),
            "mention_count": count,
            "signal_source": "Reddit news sentiment",
        }

        ai_result = confirm_signal(
            symbol=symbol,
            signal=signal,
            indicators=indicators,
            strategy_name="News Sentiment",
        )

        if ai_result["confirmed"] and ai_result["confidence"] >= 50:
            price = get_price(symbol)
            execute_trade(
                symbol=symbol,
                side=signal,
                bot_name="bot7_news",
                price=price,
                reason=f"Sentiment={avg_score:.0f} mentions={count} | AI: {ai_result['reasoning']}",
            )
            trades_made += 1
            print(f"  TRADE: {signal} {symbol} @ {price}")
        else:
            print(f"  AI rejected {symbol}: {ai_result['reasoning']}")

    print(f"Bot 7 complete. {trades_made} trades from {len(candidates)} sentiment signals.")
