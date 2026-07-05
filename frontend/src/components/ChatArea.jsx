import ChatBubble from "./ChatBubble";

function ChatArea({ chats, loading, chatEndRef }) {
    return (
        <section className="chat-area">
            {chats.map((chat, index) => (
                <ChatBubble
                    key={index}
                    sender={chat.sender}
                    text={chat.text}
                    time={chat.time}
                />
            ))}

            {loading && (
                <div className="chat-row bot">
                    <div className="avatar">AI</div>

                    <div className="bubble bot typing">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            )}

            <div ref={chatEndRef}></div>
        </section>
    );
}

export default ChatArea;