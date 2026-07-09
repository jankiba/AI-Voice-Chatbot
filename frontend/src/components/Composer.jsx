function Composer({
    message,
    setMessage,
    handleTextSend,
    handleVoiceClick,
    isRecording,
    language,
    setLanguage,
    stopBotAudio,
    botStatus,
}) {
    return (
        <footer className="composer">
            <select
                className="language-select"
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
            >
                <option value="auto">Auto</option>
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="gu">Gujarati</option>
            </select>

            <button
                className={`mic-button ${isRecording ? "recording" : ""}`}
                onClick={handleVoiceClick}
            >
                {isRecording ? "■" : "🎤"}
            </button>
            {botStatus === "speaking" && (
                <button
                    className="stop-button"
                    onClick={stopBotAudio}
                >
                    Stop
                </button>
            )}

            <input
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ask me anything..."
                onKeyDown={(e) => e.key === "Enter" && handleTextSend()}
            />

            {message.trim() && (
                <button className="send-button" onClick={handleTextSend}>
                    ➜
                </button>
            )}
        </footer>
    );
}

export default Composer;