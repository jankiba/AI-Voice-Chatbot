import os
import re

from faster_whisper import WhisperModel
from groq import Groq

from app.config import GROQ_API_KEY
from app.language_service import normalize_language

WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "small")
STT_PROVIDER = os.getenv("STT_PROVIDER", "groq")
GROQ_STT_MODEL = os.getenv("GROQ_STT_MODEL", "whisper-large-v3-turbo")
ENABLE_TRANSCRIPT_CORRECTION = (
    os.getenv("ENABLE_TRANSCRIPT_CORRECTION", "true").lower() == "true"
)

groq_client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None
local_model = None

LANGUAGE_PROMPTS = {
    "gu": (
        "આ ગુજરાતી ભાષાનું વોઇસ મેસેજ છે. કૃપા કરીને ગુજરાતી લિપિમાં ચોક્કસ રીતે લખો. "
        "Common phrases: kem cho = કેમ છો, tame kem cho = તમે કેમ છો, "
        "hu majama chu = હું મજામાં છું, shu karo cho = શું કરો છો."
    ),
    "hi": (
        "यह हिंदी भाषा का वॉइस मैसेज है। कृपया हिंदी लिपि में सही लिखें। "
        "Common phrases: kaise ho = कैसे हो, tum kaise ho = तुम कैसे हो, "
        "main theek hoon = मैं ठीक हूँ, kya kar rahe ho = क्या कर रहे हो."
    ),
    "en": "This is an English voice message. Please transcribe it accurately.",
    "auto": (
        "This voice message may be English, Hindi, Gujarati, Roman Hindi, "
        "or Roman Gujarati. Transcribe it in the language the speaker used."
    ),
}

TRANSCRIPT_FIXES = {
    "en": {
        "goodling": "good morning",
        "gud ling": "good morning",
        "góð í líng": "good morning",
        "hey der": "hey there",
    },
    "gu": {
        "મેકે છોડ": "કેમ છો",
        "મેકે છો": "કેમ છો",
        "મે કે છો": "કેમ છો",
        "કેમ ચો": "કેમ છો",
        "કેમ છો તમે": "તમે કેમ છો",
        "કેમ છો ત્મે": "તમે કેમ છો",
        "કેમ છો તમે?": "તમે કેમ છો?",
        "કેમ છો ત્મે?": "તમે કેમ છો?",
        "મજા માં છું": "મજામાં છું",
        "હું મજા માં છું": "હું મજામાં છું",
    },
    "hi": {
        "कैसे हों": "कैसे हो",
        "कैसा हो": "कैसे हो",
        "तुम कैसा हो": "तुम कैसे हो",
        "मैं ठीक हूं": "मैं ठीक हूँ",
        "क्या कर रहे हों": "क्या कर रहे हो",
    },
}


def get_local_model():
    global local_model

    if local_model is None:
        local_model = WhisperModel(
            WHISPER_MODEL_SIZE,
            device="cpu",
            compute_type="int8"
        )

    return local_model


def transcribe_with_groq(audio_path: str, language: str):
    if not groq_client:
        raise RuntimeError("GROQ_API_KEY is missing")

    normalized_language = normalize_language(language)
    transcription_args = {
        "model": GROQ_STT_MODEL,
        "response_format": "json",
        "temperature": 0,
        "prompt": LANGUAGE_PROMPTS.get(normalized_language),
    }

    if normalized_language != "auto":
        transcription_args["language"] = normalized_language

    with open(audio_path, "rb") as audio_file:
        transcription = groq_client.audio.transcriptions.create(
            file=audio_file,
            **transcription_args
        )

    return transcription.text.strip()


def strip_terminal_punctuation(text: str):
    return re.sub(r"[\s.?!।]+$", "", text.strip())


def apply_transcript_fixes(text: str, language: str):
    normalized_language = normalize_language(language)
    fixed_text = text.strip()
    lookup_text = strip_terminal_punctuation(fixed_text).lower()

    for wrong, right in TRANSCRIPT_FIXES.get(normalized_language, {}).items():
        if lookup_text == strip_terminal_punctuation(wrong).lower():
            punctuation = ""
            if fixed_text.endswith("?"):
                punctuation = "?"
            elif fixed_text.endswith("।"):
                punctuation = "।"
            elif fixed_text.endswith("."):
                punctuation = "."

            return right + punctuation

    return fixed_text


def should_correct_transcript(text: str, language: str):
    normalized_language = normalize_language(language)
    if normalized_language not in {"gu", "hi"}:
        return False

    words = text.split()
    return 0 < len(words) <= 10


def correct_short_transcript(text: str, language: str):
    if not groq_client or not should_correct_transcript(text, language):
        return text

    normalized_language = normalize_language(language)
    language_name = "Gujarati" if normalized_language == "gu" else "Hindi"
    script_name = "Gujarati" if normalized_language == "gu" else "Devanagari"

    examples = (
        "kem cho = કેમ છો, tame kem cho = તમે કેમ છો, hu majama chu = હું મજામાં છું"
        if normalized_language == "gu"
        else "kaise ho = कैसे हो, tum kaise ho = तुम कैसे हो, main theek hoon = मैं ठीक हूँ"
    )

    response = groq_client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {
                "role": "system",
                "content": (
                    f"You correct short {language_name} speech-to-text transcripts. "
                    f"Return only the corrected transcript in {script_name} script. "
                    "Do not answer the user. Do not add new meaning. "
                    "If the transcript is already correct, return it unchanged. "
                    f"Common spoken phrase examples: {examples}."
                ),
            },
            {"role": "user", "content": text},
        ],
        temperature=0,
        max_tokens=60,
    )

    corrected = response.choices[0].message.content.strip()
    return corrected or text


def clean_transcript(text: str, language: str):
    fixed_text = apply_transcript_fixes(text, language)
    if not ENABLE_TRANSCRIPT_CORRECTION:
        return fixed_text

    try:
        return correct_short_transcript(fixed_text, language)
    except Exception as exc:
        print(f"Transcript correction failed, using raw transcript: {exc}")
        return fixed_text


def transcribe_with_local_whisper(audio_path: str, language: str):
    model = get_local_model()
    normalized_language = normalize_language(language)
    whisper_language = None if normalized_language == "auto" else normalized_language

    transcribe_kwargs = {
        "task": "transcribe",
        "beam_size": 1,
        "vad_filter": True,
        "initial_prompt": LANGUAGE_PROMPTS.get(normalized_language),
    }

    if whisper_language:
        transcribe_kwargs["language"] = whisper_language

    segments, info = model.transcribe(
        audio_path,
        **transcribe_kwargs
    )

    text = ""

    for segment in segments:
        text += segment.text + " "

    return text.strip()


def speech_to_text(audio_path: str, language: str = "auto"):
    transcript = None

    if STT_PROVIDER == "groq":
        try:
            transcript = transcribe_with_groq(audio_path, language)
        except Exception as exc:
            print(f"Groq transcription failed, using local Whisper: {exc}")

    if transcript is None:
        transcript = transcribe_with_local_whisper(audio_path, language)

    return clean_transcript(transcript, language)
