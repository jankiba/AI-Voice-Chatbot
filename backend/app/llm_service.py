from groq import Groq
from app.config import GROQ_API_KEY
from app.prompts import VOICE_CHATBOT_PERSONALITY
from app.memory_service import add_message, get_history
from app.language_service import (
    contains_language_script,
    detect_language,
    get_language_name,
    normalize_language,
)
from app.tool_service import run_tool_if_needed
from app.emotion_service import detect_emotion

client = Groq(api_key=GROQ_API_KEY)


def generate_emotional_reply(user_message: str, language: str = "auto"):
    selected_language = normalize_language(language)
    detected_language = (
        selected_language
        if selected_language != "auto"
        else detect_language(user_message)
    )
    emotion = detect_emotion(user_message)
    language_name = get_language_name(detected_language)

    language_instruction = f"""
Detected user mood: {emotion}.
Match this mood naturally in your reply.
Latest user message language: {language_name}.

Rules:
- Reply only in {language_name}.
- If Gujarati, use Gujarati script only.
- If Hindi, use Hindi script only.
- If English, use English only.
- Do not mix languages.
- Do not mention language detection.
- Keep reply short, friendly, and spoken.
- For voice chat, use one or two short natural sentences, ideally under 18 words total.
- Reply like a real person, not a formal assistant.
- Keep it casual, warm, and natural.
- Use tiny conversational reactions only when they fit: "hmm," "ohh," "wait," "haha,".
- Add a small follow-up question when the user is sharing something personal.
- Use commas or short pauses so text-to-speech sounds less flat.
- Avoid robotic phrases like "How can I assist you today?"
"""

    tool_response = run_tool_if_needed(user_message)
    if tool_response:
        language_instruction += f"""
Useful factual result:
{tool_response}

Use the factual result above, but rewrite it naturally in {language_name}.
"""

    messages = [
        {
            "role": "system",
            "content": VOICE_CHATBOT_PERSONALITY + "\n\n" + language_instruction
        }
    ]

    messages.extend(get_history(limit=4))
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        temperature=0.68,
        max_tokens=55
    )

    bot_reply = response.choices[0].message.content

    if not contains_language_script(bot_reply, detected_language):
        retry_messages = messages + [
            {"role": "assistant", "content": bot_reply},
            {
                "role": "user",
                "content": (
                    f"Rewrite your last reply only in {language_name}. "
                    "Use the correct native script and do not add any English words."
                )
            },
        ]

        retry_response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=retry_messages,
            temperature=0.4,
            max_tokens=38
        )
        bot_reply = retry_response.choices[0].message.content

    add_message("user", user_message)
    add_message("assistant", bot_reply)

    return bot_reply
