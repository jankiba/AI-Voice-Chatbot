import re

def detect_language(text: str) -> str:
    text_lower = text.lower().strip()

    roman_gujarati_phrases = [
        "kem cho", "maja ma", "shu che", "su che", "saru che",
        "maru", "tamaru", "tame", "hu", "mane", "aabhar"
    ]

    roman_hindi_phrases = [
        "kaise ho", "kese ho", "namaste", "kya", "mera",
        "mujhe", "accha", "acha", "haan", "nahi", "tum", "main"
    ]

    for phrase in roman_gujarati_phrases:
        if re.search(rf"\b{re.escape(phrase)}\b", text_lower):
            return "gu"

    for phrase in roman_hindi_phrases:
        if re.search(rf"\b{re.escape(phrase)}\b", text_lower):
            return "hi"

    for char in text:
        if "\u0A80" <= char <= "\u0AFF":
            return "gu"

    for char in text:
        if "\u0900" <= char <= "\u097F":
            return "hi"

    return "en"


def get_language_name(lang_code: str) -> str:
    languages = {
        "en": "English",
        "hi": "Hindi",
        "gu": "Gujarati"
    }
    return languages.get(lang_code, "English")