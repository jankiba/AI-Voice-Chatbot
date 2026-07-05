from gtts import gTTS
import uuid
import os

from app.language_service import detect_language

OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def text_to_speech(text: str):
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    lang = detect_language(text)

    tts = gTTS(text=text, lang=lang)
    tts.save(filepath)

    return filepath