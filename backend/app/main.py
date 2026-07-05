import os
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.llm_service import generate_emotional_reply
from app.tts_service import text_to_speech
from app.memory_service import get_history, clear_history
from app.whisper_service import speech_to_text
from app.conversation_service import handle_voice_chat


app = FastAPI(title="Voice Chatbot", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str


class TTSRequest(BaseModel):
    text: str


@app.get("/")
def home():
    return {"message": "Voice Chatbot API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/text-chat")
def text_chat(request: ChatRequest):
    reply = generate_emotional_reply(request.message)
    return {
        "user_message": request.message,
        "bot_reply": reply
    }


@app.post("/text-to-speech")
def convert_text_to_speech(request: TTSRequest):
    audio_path = text_to_speech(request.text)
    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename="voice_response.mp3"
    )


@app.get("/chat-history")
def chat_history():
    return {"history": get_history()}


@app.delete("/clear-history")
def delete_history():
    clear_history()
    return {"message": "Chat history cleared"}


@app.post("/speech-to-text")
async def convert_speech_to_text(file: UploadFile = File(...)):
    audio_path = f"temp_{file.filename}"

    with open(audio_path, "wb") as buffer:
        buffer.write(await file.read())

    text = speech_to_text(audio_path)

    return {"transcribed_text": text}


@app.post("/voice-chat")
async def voice_chat(file: UploadFile = File(...)):
    result = await handle_voice_chat(file)

    filename = os.path.basename(result["bot_audio_path"])
    audio_url = f"http://127.0.0.1:8000/audio/{filename}"

    return {
        "user_text": result["user_text"],
        "bot_reply": result["bot_reply"],
        "audio_url": audio_url
    }


@app.get("/audio/{filename}")
def get_audio(filename: str):
    audio_path = os.path.abspath(os.path.join("audio", filename))

    if not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=filename
    )