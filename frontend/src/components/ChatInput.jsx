function ChatInput({
    message,
    setMessage,
    handleTextSend,
    handleVoiceClick,
    isRecording,
}) {
    return (
        <footer className="composer">
            <button
                className={`mic-btn ${isRecording ? "recording" : ""}`}
                onClick={handleVoiceClick}
            >
                {isRecording ? "⏹️" : "🎤"}
            </button>

            <input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Type your message..."
                onKeyDown={(e) => e.key === "Enter" && handleTextSend()}
            />

            <button className="send-btn" onClick={handleTextSend}>
                Send
            </button>
        </footer>
    );
}

export default ChatInput;