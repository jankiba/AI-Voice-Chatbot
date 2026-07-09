import os
import uuid
import asyncio
import edge_tts

from app.language_service import detect_language, normalize_language

OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

EDGE_VOICES = {
    "en": "en-US-EmmaMultilingualNeural",
    "hi": "hi-IN-SwaraNeural",
    "gu": "gu-IN-DhwaniNeural",
}


async def _generate_edge_voice(text: str, filepath: str, lang: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=EDGE_VOICES.get(lang, EDGE_VOICES["en"]),
        rate="-4%",
        pitch="+0Hz"
    )
    await communicate.save(filepath)


def generate_edge_tts(text: str, language: str = "auto"):
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)
    selected_language = normalize_language(language)
    lang = selected_language if selected_language != "auto" else detect_language(text)

    asyncio.run(_generate_edge_voice(text, filepath, lang))

    return filepath
