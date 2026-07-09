MAX_CONVERSATION_MESSAGES = 10

conversation_history = []


def add_message(role: str, message: str):
    conversation_history.append({
        "role": role,
        "content": message
    })

    if len(conversation_history) > MAX_CONVERSATION_MESSAGES:
        conversation_history.pop(0)


def get_history(limit: int = MAX_CONVERSATION_MESSAGES):
    return conversation_history[-limit:]


def clear_history():
    conversation_history.clear()
    
