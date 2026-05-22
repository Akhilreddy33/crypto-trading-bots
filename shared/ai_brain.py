import os
import json
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")


def _build_prompt(symbol: str, signal: str, summary: str) -> str:
    return (
        f"You are a crypto trading assistant.\n"
        f"Symbol: {symbol}\n"
        f"Signal: {signal}\n"
        f"Summary: {summary}\n"
        f"Answer only with YES or NO. Is this a strong valid trade signal?"
    )


def _build_sentiment_prompt(title: str, body: str) -> str:
    return (
        "You are a crypto news sentiment classifier.\n"
        f"Title: {title}\n"
        f"Body: {body}\n"
        "Respond with one word: BULLISH, BEARISH, or NEUTRAL."
    )


def _call_groq(prompt: str) -> str:
    if not GROQ_API_KEY:
        return ""
    try:
        import groq
        client = groq.Groq(api_key=GROQ_API_KEY)
        response = client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
        )
        if response.choices and response.choices[0].message.content:
            return response.choices[0].message.content.strip()
    except Exception:
        pass
    return ""


def confirm_signal(symbol: str, signal: str, summary: str) -> bool:
    prompt = _build_prompt(symbol, signal, summary)
    text = _call_groq(prompt)
    if not text:
        return _fallback_confirmation(signal)
    return "YES" in text.upper()


def analyze_news_sentiment(title: str, body: str) -> str:
    prompt = _build_sentiment_prompt(title, body)
    text = _call_groq(prompt)
    if not text:
        lower = (title + " " + body).lower()
        if any(k in lower for k in ["moon", "bull", "breakout", "green", "surge"]):
            return "BULLISH"
        if any(k in lower for k in ["dump", "bear", "crash", "red", "selloff"]):
            return "BEARISH"
        return "NEUTRAL"

    answer = text.strip().upper()
    if "BULL" in answer:
        return "BULLISH"
    if "BEAR" in answer:
        return "BEARISH"
    return "NEUTRAL"


def _fallback_confirmation(signal: str) -> bool:
    return signal.lower() in {"buy", "strong buy", "sell", "strong sell"}


def signal_summary(df_summary: dict) -> str:
    return json.dumps(df_summary)
