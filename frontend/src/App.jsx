import { useEffect, useRef, useState } from "react";
import { sendTextMessage, sendVoiceMessage } from "./api";
import Header from "./components/Header";
import Hero from "./components/Hero";
import ChatArea from "./components/ChatArea";
import Composer from "./components/Composer";
import "./App.css";

function App() {
  const [message, setMessage] = useState("");
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [botStatus, setBotStatus] = useState("idle");

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chats, loading]);

  const getTime = () =>
    new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

  const addChat = (sender, text) => {
    setChats((prev) => [...prev, { sender, text, time: getTime() }]);
  };

  const streamReply = async (text) => {
    const words = text.split(" ");

    setBotStatus("speaking");

    setChats((prev) => [
      ...prev,
      {
        sender: "bot",
        text: "",
        time: getTime(),
      },
    ]);

    for (let i = 0; i < words.length; i++) {
      await new Promise((resolve) => setTimeout(resolve, 60));

      setChats((prev) => {
        const updated = [...prev];
        const last = updated[updated.length - 1];

        updated[updated.length - 1] = {
          ...last,
          text: last.text === "" ? words[i] : `${last.text} ${words[i]}`,
        };

        return updated;
      });
    }

    setBotStatus("idle");
  };

  const handleNewChat = async () => {
    setChats([]);
    setMessage("");
    setLoading(false);
    setIsRecording(false);
    setBotStatus("idle");

    try {
      await fetch("http://127.0.0.1:8000/clear-history", {
        method: "DELETE",
      });
    } catch {
      console.log("Could not clear backend history");
    }
  };

  const handleTextSend = async () => {
    if (!message.trim()) return;

    const userMessage = message;
    setMessage("");

    addChat("user", userMessage);
    setLoading(true);
    setBotStatus("thinking");

    try {
      const data = await sendTextMessage(userMessage);
      setLoading(false);
      await streamReply(data.bot_reply);
    } catch {
      setLoading(false);
      await streamReply("Oops, I couldn’t connect properly. Try again?");
    }
  };

  const handleVoiceClick = async () => {
    if (!isRecording) {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        audioChunksRef.current.push(event.data);
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });

        setLoading(true);
        setBotStatus("thinking");

        try {
          const data = await sendVoiceMessage(audioBlob);

          addChat("user", data.user_text);

          setLoading(false);
          await streamReply(data.bot_reply);

          const audio = new Audio(data.audio_url);
          setBotStatus("speaking");
          audio.onended = () => setBotStatus("idle");
          audio.play();
        } catch {
          setLoading(false);
          await streamReply("I had trouble hearing that. Try again?");
          setBotStatus("idle");
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
      setBotStatus("listening");
    } else {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setBotStatus("thinking");
    }
  };

  return (
    <div className="app">
      <Header onNewChat={handleNewChat} />

      <main className="main">
        <Hero botStatus={botStatus} hasChats={chats.length > 0} />

        <ChatArea chats={chats} loading={loading} chatEndRef={chatEndRef} />
      </main>

      <Composer
        message={message}
        setMessage={setMessage}
        handleTextSend={handleTextSend}
        handleVoiceClick={handleVoiceClick}
        isRecording={isRecording}
      />
    </div>
  );
}

export default App;