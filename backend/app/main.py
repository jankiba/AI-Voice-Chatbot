import os
import uuid

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from app.llm_service import generate_emotional_reply
from app.tts_service import stream_speech, text_to_speech
from app.memory_service import get_history, clear_history
from app.whisper_service import speech_to_text
from app.conversation_service import handle_voice_chat

app = FastAPI(
    title="Voice Chatbot",
    version="1.0.0"
)

AUDIO_JOBS = {}
SPEECH_JOBS = {}
BACKEND_PUBLIC_URL = os.getenv("BACKEND_PUBLIC_URL", "http://127.0.0.1:8001")


def format_backend_error(exc: Exception):
    message = str(exc)

    if "invalid_api_key" in message or "Invalid API Key" in message:
        return "Groq API key is invalid. Update GROQ_API_KEY in backend/.env and restart the backend."

    return message


def generate_audio_job(job_id: str, text: str, language: str):
    try:
        audio_path = text_to_speech(text, language)
        filename = os.path.basename(audio_path)
        AUDIO_JOBS[job_id] = {
            "status": "ready",
            "audio_url": f"{BACKEND_PUBLIC_URL}/audio/{filename}"
        }
    except Exception as exc:
        AUDIO_JOBS[job_id] = {
            "status": "failed",
            "error": str(exc)
        }

# -----------------------------
# CORS
# -----------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# -----------------------------
# Request Models
# -----------------------------
class ChatRequest(BaseModel):
    message: str
    language: str = "auto"


class TTSRequest(BaseModel):
    text: str
    language: str = "auto"


# -----------------------------
# Home
# -----------------------------
@app.get("/")
def home():
    return {
        "message": "Voice Chatbot API is running 🚀"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# -----------------------------
# Text Chat
# -----------------------------
@app.post("/text-chat")
def text_chat(request: ChatRequest):
    try:
        reply = generate_emotional_reply(request.message, request.language)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=format_backend_error(exc)
        ) from exc

    return {
        "user_message": request.message,
        "bot_reply": reply
    }


# -----------------------------
# Text To Speech
# -----------------------------
@app.post("/text-to-speech")
def convert_text_to_speech(request: TTSRequest):

    try:
        audio_path = text_to_speech(request.text, request.language)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=format_backend_error(exc)
        ) from exc

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename="voice_response.mp3"
    )


# -----------------------------
# Speech To Text
# -----------------------------
@app.post("/speech-to-text")
async def convert_speech_to_text(
    file: UploadFile = File(...),
    language: str = Form("auto")
):

    audio_path = f"temp_{file.filename}"

    with open(audio_path, "wb") as buffer:
        buffer.write(await file.read())

    try:
        text = speech_to_text(audio_path, language)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=format_backend_error(exc)
        ) from exc
    finally:
        if os.path.exists(audio_path):
            os.remove(audio_path)

    return {
        "transcribed_text": text
    }


# -----------------------------
# Voice Chat
# -----------------------------
@app.post("/voice-chat")
async def voice_chat(
    file: UploadFile = File(...),
    language: str = Form("auto")
):

    try:
        result = await handle_voice_chat(file, language)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Voice chat failed: {format_backend_error(exc)}"
        ) from exc

    speech_job_id = str(uuid.uuid4())
    SPEECH_JOBS[speech_job_id] = {
        "text": result["bot_reply"],
        "language": language
    }

    return {
        "user_text": result["user_text"],
        "bot_reply": result["bot_reply"],
        "audio_stream_url": f"{BACKEND_PUBLIC_URL}/speak/{speech_job_id}"
    }


@app.get("/speak/{job_id}")
async def speak(job_id: str):
    job = SPEECH_JOBS.get(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Speech job not found"
        )

    return StreamingResponse(
        stream_speech(job["text"], job["language"]),
        media_type="audio/mpeg"
    )


@app.get("/audio-status/{job_id}")
def audio_status(job_id: str):
    job = AUDIO_JOBS.get(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Audio job not found"
        )

    return job


# -----------------------------
# Chat History
# -----------------------------
@app.get("/chat-history")
def chat_history():
    return {
        "history": get_history()
    }


@app.delete("/clear-history")
def delete_history():
    clear_history()

    return {
        "message": "Chat history cleared"
    }


# -----------------------------
# Audio Endpoint
# -----------------------------
@app.get("/audio/{filename}")
def get_audio(filename: str):

    audio_path = os.path.abspath(
        os.path.join("audio", filename)
    )

    if not os.path.exists(audio_path):
        raise HTTPException(
            status_code=404,
            detail="Audio file not found"
        )

    return FileResponse(
        path=audio_path,
        media_type="audio/mpeg",
        filename=filename
    )
