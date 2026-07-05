function ChatBubble({ sender, text, time }) {
    return (
        <div className={`chat-row ${sender}`}>
            <div className="avatar">
                {sender === "user" ? "You" : "AI"}
            </div>

            <div className="message-block">
                <div className={`bubble ${sender}`}>
                    {text}
                </div>

                <small>{time}</small>
            </div>
        </div>
    );
}

export default ChatBubble;