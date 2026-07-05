function Composer({
    message,
    setMessage,
    handleTextSend,
    handleVoiceClick,
    isRecording,
}) {
    return (
        <footer className="composer">
            <button
                className={`mic-button ${isRecording ? "recording" : ""}`}
                onClick={handleVoiceClick}
            >
                {isRecording ? "■" : "🎤"}
            </button>

            <input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask me anything..."
                onKeyDown={(e) =>
                    e.key === "Enter" && handleTextSend()
                }
            />

            {message.trim() && (
                <button
                    className="send-button"
                    onClick={handleTextSend}
                >
                    ➜
                </button>
            )}
        </footer>
    );
}

export default Composer;