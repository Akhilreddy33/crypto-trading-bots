"""Dashboard for bot activity and log summaries."""

import json
import os
from collections import deque
from glob import glob


LOG_FOLDER = os.path.join(os.path.dirname(__file__), "logs")


def tail(path: str, lines: int = 10) -> list[str]:
    result = deque(maxlen=lines)
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            result.append(line.rstrip("\n"))
    return list(result)


def summarize_log(path: str) -> dict:
    summary = {
        "file": os.path.basename(path),
        "total_lines": 0,
        "last_trades": [],
        "json_entries": 0,
    }
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            summary["total_lines"] += 1
            stripped = line.strip()
            if stripped.endswith("}") and "{" in stripped:
                try:
                    json.loads(stripped.split("|", 1)[1].strip())
                    summary["json_entries"] += 1
                except Exception:
                    pass
    summary["last_trades"] = tail(path, 5)
    return summary


def show_dashboard():
    log_files = glob(os.path.join(LOG_FOLDER, "*.log"))
    if not log_files:
        print("No bot logs found. Run a bot first.")
        return

    print("=== Crypto Trading Bot Dashboard ===")
    for path in sorted(log_files):
        summary = summarize_log(path)
        print(f"\nBot: {summary['file']}")
        print(f"  Total log entries: {summary['total_lines']}")
        print(f"  JSON trade entries: {summary['json_entries']}")
        print("  Last trades:")
        for line in summary["last_trades"]:
            print(f"    {line}")


if __name__ == "__main__":
    show_dashboard()
