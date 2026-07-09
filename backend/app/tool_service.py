import re
import math
from datetime import datetime

from app.weather_service import get_live_weather
from app.search_service import web_search


def calculate_expression(message: str):
    try:
        expression = message.lower()

        trigger_words = ["calculate", "what is", "solve"]
        has_math_operator = any(op in expression for op in ["+", "-", "*", "/", "×", "x"])

        if not any(word in expression for word in trigger_words) and not has_math_operator:
            return None

        expression = expression.replace("calculate", "")
        expression = expression.replace("what is", "")
        expression = expression.replace("solve", "")
        expression = expression.replace("×", "*")
        expression = expression.replace("x", "*")

        if not re.search(r"[0-9]", expression):
            return None

        allowed = "0123456789+-*/(). "
        if any(ch not in allowed for ch in expression):
            return None

        result = eval(expression, {"__builtins__": None}, {"math": math})
        return f"The answer is {result}."
    except Exception:
        return None


def get_weather_response(message: str):
    msg = message.lower()

    weather_keywords = [
        "weather",
        "temperature",
        "temp",
        "rain",
        "raining",
        "forecast"
    ]

    if not any(keyword in msg for keyword in weather_keywords):
        return None

    return get_live_weather(message)


def get_search_response(message: str):
    msg = message.lower()

    search_keywords = [
        "latest",
        "news",
        "current",
        "yesterday",
        "who won",
        "winner",
        "result",
        "score",
        "price",
        "stock",
        "bitcoin",
        "f1",
        "formula",
        "grand prix",
        "cricket",
        "football",
        "ipl",
        "nba",
        "update",
        "breaking"
    ]

    if any(keyword in msg for keyword in search_keywords):
        return web_search(message)

    return None


def get_time_date_response(message: str):
    msg = message.lower()
    now = datetime.now()

    time_date_keywords = [
        "what time is it",
        "current time",
        "time now",
        "what's the time",
        "what is the time",
        "today's date",
        "what is today's date",
        "current date",
        "date today",
        "what day is it",
        "which day is today",
    ]

    if not any(keyword in msg for keyword in time_date_keywords):
        return None

    parts = []

    if "day" in msg:
        parts.append(f"Today is {now.strftime('%A')}")

    if "date" in msg:
        parts.append(f"Today's date is {now.strftime('%d %B %Y')}")

    if "time" in msg:
        parts.append(f"The current time is {now.strftime('%I:%M %p')}")

    return ". ".join(parts) + "."


def run_tool_if_needed(message: str):
    calculator_result = calculate_expression(message)
    if calculator_result:
        return calculator_result

    weather_result = get_weather_response(message)
    if weather_result:
        return weather_result

    search_result = get_search_response(message)
    if search_result:
        return search_result

    time_date_result = get_time_date_response(message)
    if time_date_result:
        return time_date_result

    return None