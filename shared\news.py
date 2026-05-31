import os
from dotenv import load_dotenv

load_dotenv()

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "CryptoBot/1.0")


def fetch_reddit_news(limit: int = 8) -> list[dict]:
    if not (REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET):
        return []

    try:
        import praw
        reddit = praw.Reddit(
            client_id=REDDIT_CLIENT_ID,
            client_secret=REDDIT_CLIENT_SECRET,
            user_agent=REDDIT_USER_AGENT,
        )
        submissions = []
        for subreddit in ["CryptoCurrency", "CryptoMarkets"]:
            for post in reddit.subreddit(subreddit).hot(limit=limit // 2):
                submissions.append({
                    "title": post.title,
                    "score": post.score,
                    "url": post.url,
                    "created": post.created_utc,
                    "selftext": post.selftext,
                })
                if len(submissions) >= limit:
                    break
            if len(submissions) >= limit:
                break
        return submissions
    except Exception:
        return []
