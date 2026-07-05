from groq import Groq
from app.config import GROQ_API_KEY
from app.prompts import VOICE_CHATBOT_PERSONALITY
from app.memory_service import add_message, get_history
from app.language_service import detect_language, get_language_name
from app.tool_service import run_tool_if_needed

client = Groq(api_key=GROQ_API_KEY)


def generate_emotional_reply(user_message: str):
    tool_response = run_tool_if_needed(user_message)
    if tool_response:
        add_message("user", user_message)
        add_message("assistant", tool_response)
        return tool_response
    detected_language = detect_language(user_message)
    language_name = get_language_name(detected_language)

    language_instruction = f"""
Latest user message language: {language_name}.

Rules:
- Reply only in {language_name}.
- If Gujarati, use Gujarati script only.
- If Hindi, use Hindi script only.
- If English, use English only.
- Do not mix languages.
- Do not mention language detection.
- Keep reply short and friendly.
"""

    messages = [
        {
            "role": "system",
            "content": VOICE_CHATBOT_PERSONALITY + "\n\n" + language_instruction
        }
    ]

    messages.extend(get_history())
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.7,
        max_tokens=180
    )

    bot_reply = response.choices[0].message.content

    add_message("user", user_message)
    add_message("assistant", bot_reply)

    return bot_reply