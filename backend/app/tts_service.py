import asyncio
import os
import time
import uuid

import edge_tts
from gtts import gTTS

from app.language_service import detect_language, normalize_language

OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

EDGE_VOICES = {
    "en": "en-US-EmmaMultilingualNeural",
    "hi": "hi-IN-SwaraNeural",
    "gu": "gu-IN-DhwaniNeural",
}

EDGE_RATE = "-4%"
EDGE_PITCH = "+0Hz"


async def generate_edge_speech(text: str, filepath: str, lang: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=EDGE_VOICES.get(lang, EDGE_VOICES["en"]),
        rate=EDGE_RATE,
        pitch=EDGE_PITCH,
    )
    await communicate.save(filepath)


async def stream_edge_speech(text: str, language: str = "auto"):
    started_at = time.perf_counter()
    first_chunk_sent = False
    selected_language = normalize_language(language)
    lang = selected_language if selected_language != "auto" else detect_language(text)
    communicate = edge_tts.Communicate(
        text=text,
        voice=EDGE_VOICES.get(lang, EDGE_VOICES["en"]),
        rate=EDGE_RATE,
        pitch=EDGE_PITCH,
    )

    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            if not first_chunk_sent:
                print(f"tts first chunk={time.perf_counter() - started_at:.2f}s")
                first_chunk_sent = True
            yield chunk["data"]


def generate_gtts_speech(text: str, filepath: str, lang: str):
    tts = gTTS(text=text, lang=lang)
    tts.save(filepath)


def text_to_speech(text: str, language: str = "auto"):
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    selected_language = normalize_language(language)
    lang = selected_language if selected_language != "auto" else detect_language(text)

    try:
        asyncio.run(generate_edge_speech(text, filepath, lang))
    except Exception as exc:
        print(f"Edge TTS failed, using gTTS fallback: {exc}")
        generate_gtts_speech(text, filepath, lang)

    return filepath
