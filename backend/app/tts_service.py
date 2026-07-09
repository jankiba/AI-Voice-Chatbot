import asyncio
import os
import re
import time
import uuid

import edge_tts
import requests
from gtts import gTTS

from app.config import (
    OPENAI_API_KEY,
    OPENAI_TTS_MODEL,
    OPENAI_TTS_VOICE,
    TTS_PROVIDER,
)
from app.language_service import detect_language, normalize_language

OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

EDGE_VOICES = {
    "en": "en-US-EmmaMultilingualNeural",
    "hi": "hi-IN-SwaraNeural",
    "gu": "gu-IN-DhwaniNeural",
}

EDGE_RATE = "-8%"
EDGE_PITCH = "-1Hz"
OPENAI_SPEECH_URL = "https://api.openai.com/v1/audio/speech"

SPOKEN_PAUSES = {
    "ohh": "ohh,",
    "hmm": "hmm,",
    "wait": "wait,",
    "haha": "haha,",
    "aww": "aww,",
}


def prepare_spoken_text(text: str, lang: str):
    spoken = " ".join(text.strip().split())

    if not spoken:
        return spoken

    if lang == "en":
        for word, replacement in SPOKEN_PAUSES.items():
            spoken = re.sub(
                rf"\b{word}\b(?![,!?])",
                replacement,
                spoken,
                flags=re.IGNORECASE,
            )

        spoken = spoken.replace("...", ", ")
        spoken = re.sub(r"\s+([,.!?])", r"\1", spoken)
        spoken = re.sub(r"([.!?]){2,}", r"\1", spoken)

    if spoken[-1] not in ".!?।":
        spoken += "."

    return spoken


def get_openai_voice_instructions(lang: str):
    language_hint = {
        "en": "English",
        "hi": "Hindi",
        "gu": "Gujarati",
    }.get(lang, "the user's language")

    return (
        f"Speak in {language_hint}. Sound warm, natural, and conversational. "
        "Use gentle pacing, slight emotion, and friendly intonation. "
        "Do not sound like a formal announcement."
    )


def openai_tts_enabled():
    return TTS_PROVIDER.lower() == "openai" and bool(OPENAI_API_KEY)


def create_openai_speech_response(text: str, lang: str, stream: bool = True):
    spoken_text = prepare_spoken_text(text, lang)
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_TTS_MODEL,
        "voice": OPENAI_TTS_VOICE,
        "input": spoken_text,
        "response_format": "mp3",
    }

    if OPENAI_TTS_MODEL not in {"tts-1", "tts-1-hd"}:
        payload["instructions"] = get_openai_voice_instructions(lang)

    response = requests.post(
        OPENAI_SPEECH_URL,
        headers=headers,
        json=payload,
        stream=stream,
        timeout=30,
    )
    response.raise_for_status()
    return response


def generate_openai_speech(text: str, filepath: str, lang: str):
    response = create_openai_speech_response(text, lang, stream=True)

    with open(filepath, "wb") as audio_file:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                audio_file.write(chunk)


def stream_openai_speech(text: str, lang: str):
    started_at = time.perf_counter()
    first_chunk_sent = False
    response = create_openai_speech_response(text, lang, stream=True)

    for chunk in response.iter_content(chunk_size=8192):
        if chunk:
            if not first_chunk_sent:
                print(f"openai tts first chunk={time.perf_counter() - started_at:.2f}s")
                first_chunk_sent = True
            yield chunk


async def generate_edge_speech(text: str, filepath: str, lang: str):
    spoken_text = prepare_spoken_text(text, lang)
    communicate = edge_tts.Communicate(
        text=spoken_text,
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
    spoken_text = prepare_spoken_text(text, lang)
    communicate = edge_tts.Communicate(
        text=spoken_text,
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


def stream_speech(text: str, language: str = "auto"):
    selected_language = normalize_language(language)
    lang = selected_language if selected_language != "auto" else detect_language(text)

    if openai_tts_enabled():
        try:
            yield from stream_openai_speech(text, lang)
            return
        except Exception as exc:
            print(f"OpenAI TTS failed, using Edge TTS fallback: {exc}")

    async_iterator = stream_edge_speech(text, language)
    loop = asyncio.new_event_loop()

    try:
        while True:
            try:
                yield loop.run_until_complete(async_iterator.__anext__())
            except StopAsyncIteration:
                break
    finally:
        loop.close()


def generate_gtts_speech(text: str, filepath: str, lang: str):
    tts = gTTS(text=text, lang=lang)
    tts.save(filepath)


def text_to_speech(text: str, language: str = "auto"):
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    selected_language = normalize_language(language)
    lang = selected_language if selected_language != "auto" else detect_language(text)

    try:
        if openai_tts_enabled():
            generate_openai_speech(text, filepath, lang)
        else:
            asyncio.run(generate_edge_speech(text, filepath, lang))
    except Exception as exc:
        if openai_tts_enabled():
            print(f"OpenAI TTS failed, using Edge TTS fallback: {exc}")
            try:
                asyncio.run(generate_edge_speech(text, filepath, lang))
            except Exception as edge_exc:
                print(f"Edge TTS failed, using gTTS fallback: {edge_exc}")
                generate_gtts_speech(text, filepath, lang)
        else:
            print(f"Edge TTS failed, using gTTS fallback: {exc}")
            generate_gtts_speech(text, filepath, lang)

    return filepath
