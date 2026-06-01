"""Groq AI integration for trade signal confirmation."""

import os
import json
from typing import Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()


def _get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key or api_key.startswith("your_"):
        raise RuntimeError("GROQ_API_KEY not configured. Set it in .env")
    return Groq(api_key=api_key)


def confirm_signal(
    symbol: str,
    signal: str,
    indicators: dict,
    strategy_name: str = "Technical Analysis",
) -> dict:
    """Ask Groq AI to confirm or reject a trading signal.

    Returns dict with keys: confirmed (bool), confidence (0-100), reasoning (str)
    """
    prompt = f"""You are a crypto trading analyst. Evaluate this trading signal.

Symbol: {symbol}
Signal: {signal}
Strategy: {strategy_name}
Indicators: {json.dumps(indicators, default=str)}

Respond ONLY in JSON format:
{{"confirmed": true/false, "confidence": 0-100, "reasoning": "brief explanation"}}

Rules:
- Be conservative. Only confirm if indicators strongly support the signal.
- If RSI > 70 and signal is BUY, reject (overbought).
- If RSI < 30 and signal is SELL, reject (oversold).
- Consider trend alignment with EMA crossovers.
- Confidence must be between 0-100.
"""

    client = _get_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=200,
    )

    text = response.choices[0].message.content.strip()

    # Parse JSON from response
    try:
        # Handle cases where model wraps in markdown code blocks
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
            text = text.strip()
        result = json.loads(text)
        return {
            "confirmed": bool(result.get("confirmed", False)),
            "confidence": int(result.get("confidence", 0)),
            "reasoning": str(result.get("reasoning", "No reasoning provided")),
        }
    except (json.JSONDecodeError, KeyError, ValueError):
        return {
            "confirmed": False,
            "confidence": 0,
            "reasoning": f"Failed to parse AI response: {text[:100]}",
        }


def analyze_sentiment(text: str) -> dict:
    """Analyze sentiment of news/social text for crypto trading.

    Returns dict with keys: sentiment (bullish/bearish/neutral), score (-100 to 100)
    """
    prompt = f"""Analyze the sentiment of this crypto-related text for trading purposes.

Text: {text}

Respond ONLY in JSON format:
{{"sentiment": "bullish"/"bearish"/"neutral", "score": -100 to 100, "reasoning": "brief"}}

Score guide: -100 = extremely bearish, 0 = neutral, 100 = extremely bullish.
"""

    client = _get_client()
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        max_tokens=150,
    )

    text_resp = response.choices[0].message.content.strip()

    try:
        if "```" in text_resp:
            text_resp = text_resp.split("```")[1]
            if text_resp.startswith("json"):
                text_resp = text_resp[4:]
            text_resp = text_resp.strip()
        result = json.loads(text_resp)
        return {
            "sentiment": result.get("sentiment", "neutral"),
            "score": int(result.get("score", 0)),
            "reasoning": str(result.get("reasoning", "")),
        }
    except (json.JSONDecodeError, KeyError, ValueError):
        return {"sentiment": "neutral", "score": 0, "reasoning": "Parse error"}
