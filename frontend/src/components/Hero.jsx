function Hero({ botStatus, hasChats }) {
    if (hasChats) return null;

    return (
        <section className="hero">
            <div className={`hero-orb ${botStatus}`}>
                <div className="hero-orb-inner">🎙️</div>
            </div>

            <h2>
                {botStatus === "idle" && "How can I help you today?"}
                {botStatus === "listening" && "I'm listening..."}
                {botStatus === "thinking" && "Thinking..."}
                {botStatus === "speaking" && "Speaking..."}
            </h2>

            <p>
                Ask anything, type a message, or tap the microphone to start talking.
            </p>
        </section>
    );
}

export default Hero;