import { useEffect, useRef, useState } from "react";
import { clearHistory, sendVoiceMessage } from "./api";
import Header from "./components/Header";
import "./App.css";

const RECORDING_FORMATS = [
  { mimeType: "audio/webm;codecs=opus", extension: "webm" },
  { mimeType: "audio/webm", extension: "webm" },
  { mimeType: "audio/mp4;codecs=mp4a.40.2", extension: "m4a" },
  { mimeType: "audio/mp4", extension: "m4a" },
];

const getSupportedRecordingFormat = () => {
  if (!window.MediaRecorder) {
    return null;
  }

  return (
    RECORDING_FORMATS.find(({ mimeType }) =>
      MediaRecorder.isTypeSupported(mimeType),
    ) || { mimeType: "", extension: "webm" }
  );
};

function App() {
  const [chats, setChats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [botStatus, setBotStatus] = useState("idle");
  const [language, setLanguage] = useState("en");
  const [lastUserText, setLastUserText] = useState("");
  const [lastBotReply, setLastBotReply] = useState("");
  const [notice, setNotice] = useState("");

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);

  useEffect(() => {
    if (!notice) return undefined;

    const timer = window.setTimeout(() => setNotice(""), 4000);
    return () => window.clearTimeout(timer);
  }, [notice]);

  const getTime = () =>
    new Date().toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });

  const addChat = (sender, text) => {
    setChats((prev) => [...prev, { sender, text, time: getTime() }]);
  };

  const statusCopy = {
    idle: "Ready",
    listening: "Listening",
    thinking: "Composing",
    speaking: "Speaking",
  };

  const helperCopy = {
    idle: "Tap the mic and speak naturally.",
    listening: "I am listening now.",
    thinking: "Preparing a short reply.",
    speaking: "Tap the orb to stop.",
  };

  const stopBotAudio = () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }

    setBotStatus("idle");
  };

  const showNotice = (message) => {
    setNotice(message);
    setLastBotReply(message);
  };

  const playAudioUrl = (audioUrl) => {
    stopBotAudio();

    const audio = new Audio(audioUrl);
    currentAudioRef.current = audio;
    setBotStatus("speaking");

    audio.onended = () => {
      currentAudioRef.current = null;
      setBotStatus("idle");
    };

    audio.onerror = () => {
      currentAudioRef.current = null;
      setBotStatus("idle");
    };

    audio.play().catch(() => {
      currentAudioRef.current = null;
      setBotStatus("idle");
    });
  };

  const handleNewChat = async () => {
    stopBotAudio();

    setChats([]);
    setLastUserText("");
    setLastBotReply("");
    setNotice("");
    setLoading(false);
    setIsRecording(false);
    setBotStatus("idle");

    try {
      await clearHistory();
    } catch {
      console.log("Could not clear backend history");
    }
  };

  const handleVoiceClick = async () => {
    if (botStatus === "speaking") {
      stopBotAudio();
      return;
    }

    stopBotAudio();

    if (!isRecording) {
      const recordingFormat = getSupportedRecordingFormat();

      if (!recordingFormat) {
        showNotice("Voice recording is not supported in this browser.");
        return;
      }

      let stream;

      try {
        stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      } catch {
        showNotice("I need microphone permission before I can listen.");
        return;
      }

      const mediaRecorder = new MediaRecorder(
        stream,
        recordingFormat.mimeType ? { mimeType: recordingFormat.mimeType } : undefined,
      );

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType || recordingFormat.mimeType,
        });
        const filename = `voice.${recordingFormat.extension}`;

        if (!audioBlob.size) {
          setLoading(false);
          showNotice("No audio was recorded. Please try again.");
          setBotStatus("idle");
          return;
        }

        setLoading(true);
        setBotStatus("thinking");

        try {
          const data = await sendVoiceMessage(audioBlob, language, filename);

          addChat("user", data.user_text);
          addChat("bot", data.bot_reply);
          setLastUserText(data.user_text);
          setLastBotReply(data.bot_reply);

          setLoading(false);
          playAudioUrl(data.audio_stream_url);
        } catch (error) {
          setLoading(false);
          showNotice(error.message || "I had trouble hearing that. Try again?");
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

      <main className="voice-main">
        <section className={`voice-shell ${botStatus}`}>
          <div className="voice-panel">
            <div className="voice-toolbar">
              <div className={`status-pill ${botStatus}`}>
                <span></span>
                {statusCopy[botStatus]}
              </div>

              <select
                className="language-select"
                value={language}
                onChange={(event) => setLanguage(event.target.value)}
              >
                <option value="en">English</option>
                <option value="hi">Hindi</option>
                <option value="gu">Gujarati</option>
              </select>
            </div>

            <div className="assistant-presence">
              <button
                className={`voice-orb ${botStatus}`}
                onClick={handleVoiceClick}
                disabled={loading && !isRecording}
                aria-label={isRecording ? "Stop recording" : "Start voice chat"}
              >
                <span className="voice-orb-core">
                  {isRecording ? "■" : "🎙️"}
                </span>
                <span className="waveform" aria-hidden="true">
                  <i></i>
                  <i></i>
                  <i></i>
                  <i></i>
                  <i></i>
                </span>
              </button>

              <div className="voice-copy">
                <p className="eyebrow">Voice session</p>
                <h2>
                  {botStatus === "idle" && "Ready when you are"}
                  {botStatus === "listening" && "I’m listening"}
                  {botStatus === "thinking" && "Thinking"}
                  {botStatus === "speaking" && "Speaking"}
                </h2>
                <p className="helper-text">{helperCopy[botStatus]}</p>
              </div>

              {botStatus === "speaking" && (
                <button className="stop-button" onClick={stopBotAudio}>
                  Stop speaking
                </button>
              )}
            </div>
          </div>

          <aside className="conversation-panel" aria-live="polite">
            <div className="panel-header">
              <div>
                <p>Live exchange</p>
                <span>{statusCopy[botStatus]}</span>
              </div>
            </div>

            <div className="voice-captions">
              <p className={!lastUserText ? "empty-caption" : ""}>
                <span>You</span>
                {lastUserText || "Waiting for your voice"}
              </p>

              <p className={!(lastBotReply || loading || notice) ? "empty-caption" : ""}>
                <span>Assistant</span>
                {loading ? "Thinking..." : lastBotReply || "Ready to reply"}
              </p>
            </div>
          </aside>
        </section>
      </main>
    </div>
  );
}

export default App;
