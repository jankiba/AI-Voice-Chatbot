import re
import requests
from app.config import OPENWEATHER_API_KEY


COMMON_WORDS = [
    "weather", "temperature", "temp", "rain", "raining",
    "today", "current", "now", "what", "whats", "what's",
    "is", "it", "in", "of", "for", "the", "tell", "me",
    "please", "city", "condition", "conditions"
]


def clean_city(city: str):
    city = city.lower()

    for word in COMMON_WORDS:
        city = re.sub(rf"\b{word}\b", "", city)

    city = re.sub(r"\s+", " ", city).strip()

    if not city:
        return None

    return city.title()


def extract_city(message: str):
    msg = message.lower().strip()

    patterns = [
        r"(?:weather|temperature|temp|rain|raining).*?\bin\s+([a-zA-Z\s]+)",
        r"(?:weather|temperature|temp|rain|raining).*?\bfor\s+([a-zA-Z\s]+)",
        r"\bin\s+([a-zA-Z\s]+).*?(?:weather|temperature|temp|rain|raining)",
        r"([a-zA-Z\s]+)\s+(?:weather|temperature|temp)",
    ]

    for pattern in patterns:
        match = re.search(pattern, msg)
        if match:
            city = clean_city(match.group(1))
            if city:
                return city

    return None

def get_live_weather(message: str):
    city = extract_city(message)

    if not city:
        return "Please tell me the city name. For example: weather in Surat."

    url = "https://api.openweathermap.org/data/2.5/weather"

    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200:
            return f"Sorry, I couldn't find live weather for {city}."

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"].title()
        wind = data["wind"]["speed"]

        rain_status = "No rain reported right now."
        if "rain" in data:
            rain_status = "Rain is reported right now."

        return (
            f"Weather in {city}: {condition}. "
            f"Temperature is {temp}°C, feels like {feels_like}°C. "
            f"Humidity is {humidity}%. Wind speed is {wind} m/s. "
            f"{rain_status}"
        )

    except Exception:
        return "Sorry, I couldn't fetch the live weather right now."