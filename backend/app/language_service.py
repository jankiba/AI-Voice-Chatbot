import re

SUPPORTED_LANGUAGES = {"en", "hi", "gu"}
LANGUAGE_NAMES = {
    "en": "English",
    "hi": "Hindi",
    "gu": "Gujarati",
}


def normalize_language(language: str) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language

    return "auto"


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


def contains_language_script(text: str, lang_code: str) -> bool:
    if lang_code == "gu":
        return any("\u0A80" <= char <= "\u0AFF" for char in text)

    if lang_code == "hi":
        return any("\u0900" <= char <= "\u097F" for char in text)

    return True


def get_language_name(lang_code: str) -> str:
    return LANGUAGE_NAMES.get(lang_code, "English")
