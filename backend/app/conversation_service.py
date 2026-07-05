import os
import uuid

from app.whisper_service import speech_to_text
from app.llm_service import generate_emotional_reply
from app.tts_service import text_to_speech


TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)


async def handle_voice_chat(file):
    input_audio_path = os.path.join(TEMP_DIR, f"{uuid.uuid4()}_{file.filename}")

    with open(input_audio_path, "wb") as buffer:
        buffer.write(await file.read())

    user_text = speech_to_text(input_audio_path)
    bot_reply = generate_emotional_reply(user_text)
    bot_audio_path = text_to_speech(bot_reply)

    return {
        "user_text": user_text,
        "bot_reply": bot_reply,
        "bot_audio_path": bot_audio_path
    }