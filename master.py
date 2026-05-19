"""Master runner for the trading bot suite."""

from bots.bot1_technical import run_bot as run_bot1
from bots.bot2_multicoin import run_bot as run_bot2
from bots.bot3_trend import run_bot as run_bot3
from bots.bot4_reversion import run_bot as run_bot4
from bots.bot5_breakout import run_bot as run_bot5
from bots.bot6_volume import run_bot as run_bot6
from bots.bot7_news import run_bot as run_bot7


def main():
    bots = [
        ("Bot 1 Technical", run_bot1),
        ("Bot 2 Multi-Coin", run_bot2),
        ("Bot 3 Trend Following", run_bot3),
        ("Bot 4 Mean Reversion", run_bot4),
        ("Bot 5 Breakout", run_bot5),
        ("Bot 6 Volume Spike", run_bot6),
        ("Bot 7 News Sentiment", run_bot7),
    ]

    print("Starting Crypto Trading Bots master runner...")
    for name, bot in bots:
        print(f"\n=== Running {name} ===")
        try:
            bot()
        except Exception as exc:
            print(f"{name} failed: {exc}")
    print("\nMaster runner finished.")


if __name__ == "__main__":
    main()
