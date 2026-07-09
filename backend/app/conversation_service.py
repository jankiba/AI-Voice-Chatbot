import os
import time
import uuid

from app.whisper_service import speech_to_text
from app.llm_service import generate_emotional_reply


TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)


async def handle_voice_chat(file, language="auto"):
    input_audio_path = os.path.join(
        TEMP_DIR,
        f"{uuid.uuid4()}_{file.filename}"
    )

    try:
        with open(input_audio_path, "wb") as buffer:
            buffer.write(await file.read())

        started_at = time.perf_counter()
        user_text = speech_to_text(input_audio_path, language)
        transcribed_at = time.perf_counter()
        if not user_text.strip():
            raise ValueError("No speech was transcribed from the recording.")

        bot_reply = generate_emotional_reply(user_text, language)
        replied_at = time.perf_counter()
        print(
            "voice timings:",
            f"stt={transcribed_at - started_at:.2f}s",
            f"reply={replied_at - transcribed_at:.2f}s",
            f"total={replied_at - started_at:.2f}s"
        )
        return {
            "user_text": user_text,
            "bot_reply": bot_reply,
        }
    finally:
        if os.path.exists(input_audio_path):
            os.remove(input_audio_path)
