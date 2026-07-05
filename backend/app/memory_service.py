conversation_history = []


def add_message(role: str, message: str):
    conversation_history.append({
        "role": role,
        "content": message
    })

    # Keep only the last 10 messages
    if len(conversation_history) > 10:
        conversation_history.pop(0)


def get_history():
    return conversation_history


def clear_history():
    conversation_history.clear()
    