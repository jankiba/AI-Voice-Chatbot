from faster_whisper import WhisperModel

model = WhisperModel("base", device="cpu", compute_type="int8")


def transcribe_with_language(audio_path: str, language=None):
    segments, info = model.transcribe(audio_path, language=language)

    text = ""
    for segment in segments:
        text += segment.text + " "

    return text.strip(), info.language


def speech_to_text(audio_path: str):
    # 1. Try automatic detection
    text, detected_lang = transcribe_with_language(audio_path)

    # 2. If Whisper thinks it is English but text looks wrong/too short,
    # try Gujarati and Hindi fallback
    if detected_lang == "en" and len(text.split()) <= 5:
        gu_text, _ = transcribe_with_language(audio_path, language="gu")
        hi_text, _ = transcribe_with_language(audio_path, language="hi")

        # Prefer Gujarati if it produces Gujarati script
        if any("\u0A80" <= ch <= "\u0AFF" for ch in gu_text):
            return gu_text

        # Prefer Hindi if it produces Devanagari script
        if any("\u0900" <= ch <= "\u097F" for ch in hi_text):
            return hi_text

    return text