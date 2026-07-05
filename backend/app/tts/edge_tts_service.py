import os
import uuid
import asyncio
import edge_tts

OUTPUT_DIR = "audio"
os.makedirs(OUTPUT_DIR, exist_ok=True)

VOICE = "en-US-AriaNeural"


async def _generate_edge_voice(text: str, filepath: str):
    communicate = edge_tts.Communicate(
        text=text,
        voice=VOICE,
        rate="+5%",
        pitch="+2Hz"
    )
    await communicate.save(filepath)


def generate_edge_tts(text: str):
    filename = f"{uuid.uuid4()}.mp3"
    filepath = os.path.join(OUTPUT_DIR, filename)

    asyncio.run(_generate_edge_voice(text, filepath))

    return filepath