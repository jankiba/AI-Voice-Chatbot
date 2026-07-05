from app.tts.edge_tts_service import generate_edge_tts


def text_to_speech(text: str):
    return generate_edge_tts(text)