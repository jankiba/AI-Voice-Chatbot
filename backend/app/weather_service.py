import re
import requests
from app.config import OPENWEATHER_API_KEY
from app.city_extractor import extract_city_with_ai


STOP_WORDS = {
    "what", "is", "the", "today", "todays", "current", "now",
    "weather", "temperature", "temp", "rain", "raining",
    "can", "could", "please", "check", "tell", "me",
    "for", "in", "of", "at", "show", "give", "city",
    "you", "u", "to", "know", "want", "does", "do"
}

CITY_ALIASES = {
    "nyc": "New York",
    "new york city": "New York",
    "la": "Los Angeles",
    "sf": "San Francisco",
    "bombay": "Mumbai",
    "calcutta": "Kolkata",
    "madras": "Chennai",
    "bangalore": "Bengaluru",
}


def clean_city(text: str):
    words = re.findall(r"[a-zA-Z]+", text.lower())
    city_words = [word for word in words if word not in STOP_WORDS]

    if not city_words:
        return None

    city = " ".join(city_words).strip()
    city = CITY_ALIASES.get(city, city)

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

    return clean_city(msg)


def get_coordinates(city: str):
    url = "https://api.openweathermap.org/geo/1.0/direct"

    query = city

    # Prefer Indian locations for short/local city names
    indian_places = ["valia", "ankleshwar", "bharuch", "surat", "vadodara"]
    if city.lower() in indian_places:
        query = f"{city},IN"

    params = {
        "q": query,
        "limit": 5,
        "appid": OPENWEATHER_API_KEY,
    }

    response = requests.get(url, params=params, timeout=10)
    data = response.json()

    if not data:
        return None

    # Prefer India if available
    for place in data:
        if place.get("country") == "IN":
            return {
                "name": place.get("name", city),
                "country": place.get("country", ""),
                "lat": place["lat"],
                "lon": place["lon"],
            }

    first = data[0]
    return {
        "name": first.get("name", city),
        "country": first.get("country", ""),
        "lat": first["lat"],
        "lon": first["lon"],
    }
def get_live_weather(message: str):
    city = extract_city_with_ai(message)

    if not city:
        return "Please tell me the city name. For example: weather in Surat."

    try:
        location = get_coordinates(city)

        if not location:
            return f"Sorry, I couldn't find live weather for {city}."

        url = "https://api.openweathermap.org/data/2.5/weather"

        params = {
            "lat": location["lat"],
            "lon": location["lon"],
            "appid": OPENWEATHER_API_KEY,
            "units": "metric",
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if response.status_code != 200:
            return f"Sorry, I couldn't fetch weather for {city}."

        temp = data["main"]["temp"]
        feels_like = data["main"]["feels_like"]
        humidity = data["main"]["humidity"]
        condition = data["weather"][0]["description"].title()
        wind = data["wind"]["speed"]

        rain_status = "No rain reported right now."
        if "rain" in data:
            rain_status = "Rain is reported right now."

        place = f"{location['name']}, {location['country']}"

        return (
            f"Weather in {place}: {condition}. "
            f"Temperature is {temp}°C, feels like {feels_like}°C. "
            f"Humidity is {humidity}%. Wind speed is {wind} m/s. "
            f"{rain_status}"
        )

    except Exception:
        return "Sorry, I couldn't fetch the live weather right now."