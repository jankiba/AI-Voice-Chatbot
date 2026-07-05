function Sidebar() {
    return (
        <aside className="sidebar">
            <div className="brand">
                <div className="brand-icon">🤖</div>
                <div>
                    <h2>Voice Chatbot</h2>
                    <p>AI Voice Assistant</p>
                </div>
            </div>

            <button className="new-chat">+ New Chat</button>

            <div className="sidebar-section">
                <p className="section-title">Features</p>
                <div className="feature">💬 Text Chat</div>
                <div className="feature">🎤 Voice Chat</div>
                <div className="feature">🧠 Memory</div>
                <div className="feature">🔊 Voice Reply</div>
            </div>
        </aside>
    );
}

export default Sidebar;