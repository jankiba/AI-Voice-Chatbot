import re
import math
from datetime import datetime
from app.weather_service import get_live_weather


def calculate_expression(message: str):
    try:
        expression = message.lower()
        expression = expression.replace("calculate", "")
        expression = expression.replace("what is", "")
        expression = expression.replace("×", "*")
        expression = expression.replace("x", "*")

        if not re.search(r"[0-9]", expression):
            return None

        allowed = "0123456789+-*/(). "
        if any(ch not in allowed for ch in expression):
            return None

        result = eval(expression, {"__builtins__": None}, {"math": math})
        return f"The answer is {result}."
    except:
        return None


def get_time_date_response(message: str):
    msg = message.lower()

    # Don't handle weather-related queries here
    if "weather" in msg or "rain" in msg or "raining" in msg:
        return None

    now = datetime.now()

    wants_time = "time" in msg
    wants_date = "date" in msg or "today" in msg
    wants_day = "day" in msg

    if wants_time or wants_date or wants_day:
        parts = []

        if wants_day:
            parts.append(f"Today is {now.strftime('%A')}")

        if wants_date:
            parts.append(f"The date is {now.strftime('%d %B %Y')}")

        if wants_time:
            parts.append(f"The current time is {now.strftime('%I:%M %p')}")

        return ". ".join(parts) + "."

    return None


def get_weather_response(message: str):
    msg = message.lower()

    weather_keywords = ["weather", "raining", "rain", "temperature", "temp"]

    if not any(word in msg for word in weather_keywords):
        return None

    return get_live_weather(message)

def run_tool_if_needed(message: str):
    calculator_result = calculate_expression(message)
    if calculator_result:
        return calculator_result

    time_date_result = get_time_date_response(message)
    if time_date_result:
        return time_date_result

    weather_result = get_weather_response(message)
    if weather_result:
        return weather_result

    return None