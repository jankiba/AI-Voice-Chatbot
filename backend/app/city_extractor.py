from groq import Groq
from app.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)


def extract_city_with_ai(message: str):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    "You extract city names from user messages. "
                    "Return ONLY one city name. "
                    "No labels, no explanation, no examples. "
                    "If no city exists, return NONE."
                ),
            },
            {
                "role": "user",
                "content": message,
            },
        ],
        temperature=0,
        max_tokens=10,
    )

    city = response.choices[0].message.content.strip()

    if city.upper() == "NONE":
        return None

    # Safety cleanup
    city = city.replace("City:", "").strip()
    city = city.split("\n")[0].strip()

    return city