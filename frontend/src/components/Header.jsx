function Header({ onNewChat }) {
    return (
        <header className="top-header">
            <div className="brand">
                <div className="brand-logo">🤖</div>

                <div>
                    <h1>Voice Chatbot</h1>
                    <p>Your personal AI assistant</p>
                </div>
            </div>

            <button className="new-chat-btn" onClick={onNewChat}>
                ✨ New Chat
            </button>
        </header>
    );
}

export default Header;