def detect_emotion(message: str) -> str:
    msg = message.lower()

    if any(word in msg for word in ["happy", "selected", "excited", "great", "amazing", "good news"]):
        return "happy"

    if any(word in msg for word in ["sad", "tired", "failed", "stress", "stressed", "worried", "nervous"]):
        return "supportive"

    if any(word in msg for word in ["angry", "frustrated", "annoyed", "irritated"]):
        return "calm"

    if any(word in msg for word in ["joke", "funny", "haha", "lol"]):
        return "playful"

    return "friendly"
    