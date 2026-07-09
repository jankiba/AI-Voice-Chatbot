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

const SILENCE_LIMIT_MS = 1300;
const MIN_SPEECH_MS = 350;
const VOICE_THRESHOLD = 0.035;

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
  const [, setChats] = useState([]);
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [botStatus, setBotStatus] = useState("idle");
  const [language, setLanguage] = useState("en");
  const [lastUserText, setLastUserText] = useState("");
  const [lastBotReply, setLastBotReply] = useState("");
  const [notice, setNotice] = useState("");
  const [conversationMode, setConversationMode] = useState("manual");
  const [handsFreeActive, setHandsFreeActive] = useState(false);

  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);
  const currentStreamRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const vadFrameRef = useRef(null);
  const interruptStreamRef = useRef(null);
  const interruptContextRef = useRef(null);
  const interruptAnalyserRef = useRef(null);
  const interruptFrameRef = useRef(null);
  const interruptStartedAtRef = useRef(null);
  const shouldSubmitRecordingRef = useRef(false);
  const speechStartedAtRef = useRef(null);
  const silenceStartedAtRef = useRef(null);
  const isSubmittingRef = useRef(false);
  const handsFreeActiveRef = useRef(false);
  const botStatusRef = useRef("idle");
  const languageRef = useRef(language);

  useEffect(() => {
    handsFreeActiveRef.current = handsFreeActive;
  }, [handsFreeActive]);

  useEffect(() => {
    botStatusRef.current = botStatus;
  }, [botStatus]);

  useEffect(() => {
    languageRef.current = language;
  }, [language]);

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
    idle:
      conversationMode === "hands-free" && handsFreeActive
        ? "Listening will restart after each reply."
        : "Tap the mic and speak naturally.",
    listening:
      conversationMode === "hands-free"
        ? "Speak naturally; I will send it after a pause."
        : "I am listening now.",
    thinking: "Preparing a short reply.",
    speaking:
      conversationMode === "hands-free"
        ? "Speak to interrupt, or tap to stop."
        : "Tap the orb to stop.",
  };

  const stopBotAudio = () => {
    cleanupInterruptionWatch();

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current.currentTime = 0;
      currentAudioRef.current = null;
    }

    setBotStatus("idle");
  };

  const cleanupInterruptionWatch = () => {
    if (interruptFrameRef.current) {
      cancelAnimationFrame(interruptFrameRef.current);
      interruptFrameRef.current = null;
    }

    if (interruptContextRef.current) {
      interruptContextRef.current.close().catch(() => {});
      interruptContextRef.current = null;
    }

    if (interruptStreamRef.current) {
      interruptStreamRef.current.getTracks().forEach((track) => track.stop());
      interruptStreamRef.current = null;
    }

    interruptAnalyserRef.current = null;
    interruptStartedAtRef.current = null;
  };

  const cleanupVad = () => {
    if (vadFrameRef.current) {
      cancelAnimationFrame(vadFrameRef.current);
      vadFrameRef.current = null;
    }

    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }

    analyserRef.current = null;
    speechStartedAtRef.current = null;
    silenceStartedAtRef.current = null;
  };

  const cleanupListening = () => {
    cleanupVad();

    if (mediaRecorderRef.current?.state === "recording") {
      shouldSubmitRecordingRef.current = false;
      mediaRecorderRef.current.stop();
    }

    mediaRecorderRef.current = null;

    if (currentStreamRef.current) {
      currentStreamRef.current.getTracks().forEach((track) => track.stop());
      currentStreamRef.current = null;
    }

    audioChunksRef.current = [];
    setIsRecording(false);
  };

  const showNotice = (message) => {
    setNotice(message);
    setLastBotReply(message);
  };

  const restartHandsFreeSoon = () => {
    if (!handsFreeActiveRef.current) return;

    window.setTimeout(() => {
      if (
        handsFreeActiveRef.current &&
        botStatusRef.current !== "listening" &&
        botStatusRef.current !== "thinking"
      ) {
        startRecording("hands-free");
      }
    }, 350);
  };

  const playAudioUrl = (audioUrl) => {
    stopBotAudio();

    const audio = new Audio(audioUrl);
    currentAudioRef.current = audio;
    setBotStatus("speaking");

    audio.onended = () => {
      cleanupInterruptionWatch();
      currentAudioRef.current = null;
      setBotStatus("idle");
      restartHandsFreeSoon();
    };

    audio.onerror = () => {
      cleanupInterruptionWatch();
      currentAudioRef.current = null;
      setBotStatus("idle");
      restartHandsFreeSoon();
    };

    audio
      .play()
      .then(startInterruptionWatch)
      .catch(() => {
        cleanupInterruptionWatch();
        currentAudioRef.current = null;
        setBotStatus("idle");
        restartHandsFreeSoon();
      });
  };

  const submitAudioBlob = async (audioBlob, recordingFormat) => {
    if (isSubmittingRef.current) return;

    const filename = `voice.${recordingFormat.extension}`;
    isSubmittingRef.current = true;
    setLoading(true);
    setBotStatus("thinking");

    try {
      const data = await sendVoiceMessage(audioBlob, languageRef.current, filename);

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
      restartHandsFreeSoon();
    } finally {
      isSubmittingRef.current = false;
    }
  };

  const getVoiceLevel = () => {
    const analyser = analyserRef.current;
    if (!analyser) return 0;

    return getAnalyserLevel(analyser);
  };

  const getAnalyserLevel = (analyser) => {
    if (!analyser) return 0;

    const samples = new Uint8Array(analyser.fftSize);
    analyser.getByteTimeDomainData(samples);

    let sum = 0;
    for (const sample of samples) {
      const centered = (sample - 128) / 128;
      sum += centered * centered;
    }

    return Math.sqrt(sum / samples.length);
  };

  const monitorInterruption = () => {
    // eslint-disable-next-line react-hooks/purity
    const now = Date.now();
    const voiceLevel = getAnalyserLevel(interruptAnalyserRef.current);

    if (voiceLevel > VOICE_THRESHOLD + 0.02) {
      if (!interruptStartedAtRef.current) {
        interruptStartedAtRef.current = now;
      }

      if (now - interruptStartedAtRef.current > 260) {
        stopBotAudio();
        startRecording("hands-free");
        return;
      }
    } else {
      interruptStartedAtRef.current = null;
    }

    interruptFrameRef.current = requestAnimationFrame(monitorInterruption);
  };

  const startInterruptionWatch = async () => {
    if (!handsFreeActiveRef.current) return;

    cleanupInterruptionWatch();

    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
      const audioContext = new AudioContext();
      const source = audioContext.createMediaStreamSource(stream);
      const analyser = audioContext.createAnalyser();

      analyser.fftSize = 1024;
      source.connect(analyser);

      interruptStreamRef.current = stream;
      interruptContextRef.current = audioContext;
      interruptAnalyserRef.current = analyser;
      interruptFrameRef.current = requestAnimationFrame(monitorInterruption);
    } catch {
      cleanupInterruptionWatch();
    }
  };

  const monitorSilence = () => {
    // eslint-disable-next-line react-hooks/purity
    const now = Date.now();
    const voiceLevel = getVoiceLevel();
    const userIsSpeaking = voiceLevel > VOICE_THRESHOLD;

    if (userIsSpeaking) {
      if (!speechStartedAtRef.current) {
        speechStartedAtRef.current = now;
      }
      silenceStartedAtRef.current = null;
    } else if (
      speechStartedAtRef.current &&
      now - speechStartedAtRef.current > MIN_SPEECH_MS
    ) {
      if (!silenceStartedAtRef.current) {
        silenceStartedAtRef.current = now;
      }

      if (now - silenceStartedAtRef.current > SILENCE_LIMIT_MS) {
        shouldSubmitRecordingRef.current = true;
        cleanupVad();

        if (mediaRecorderRef.current?.state === "recording") {
          mediaRecorderRef.current.stop();
        }
        return;
      }
    }

    vadFrameRef.current = requestAnimationFrame(monitorSilence);
  };

  const attachVad = (stream) => {
    cleanupVad();

    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) {
      showNotice("Hands-free listening is not supported in this browser.");
      return false;
    }

    const audioContext = new AudioContext();
    const source = audioContext.createMediaStreamSource(stream);
    const analyser = audioContext.createAnalyser();

    analyser.fftSize = 1024;
    source.connect(analyser);

    audioContextRef.current = audioContext;
    analyserRef.current = analyser;
    vadFrameRef.current = requestAnimationFrame(monitorSilence);
    return true;
  };

  const startRecording = async (mode = conversationMode) => {
    if (mediaRecorderRef.current?.state === "recording") {
      return;
    }

    const recordingFormat = getSupportedRecordingFormat();

    if (!recordingFormat) {
      showNotice("Voice recording is not supported in this browser.");
      return;
    }

    let stream;

    try {
      stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
      });
    } catch {
      showNotice("I need microphone permission before I can listen.");
      if (mode === "hands-free") {
        setHandsFreeActive(false);
      }
      return;
    }

    const mediaRecorder = new MediaRecorder(
      stream,
      recordingFormat.mimeType ? { mimeType: recordingFormat.mimeType } : undefined,
    );

    currentStreamRef.current = stream;
    mediaRecorderRef.current = mediaRecorder;
    audioChunksRef.current = [];
    shouldSubmitRecordingRef.current = mode === "manual";

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        audioChunksRef.current.push(event.data);
      }
    };

    mediaRecorder.onstop = async () => {
      const shouldSubmit = shouldSubmitRecordingRef.current;
      const audioBlob = new Blob(audioChunksRef.current, {
        type: mediaRecorder.mimeType || recordingFormat.mimeType,
      });

      cleanupVad();

      if (currentStreamRef.current) {
        currentStreamRef.current.getTracks().forEach((track) => track.stop());
        currentStreamRef.current = null;
      }

      mediaRecorderRef.current = null;
      audioChunksRef.current = [];
      setIsRecording(false);

      if (!shouldSubmit) {
        if (handsFreeActiveRef.current && botStatusRef.current !== "speaking") {
          setBotStatus("idle");
        }
        return;
      }

      if (!audioBlob.size) {
        setLoading(false);
        showNotice("No audio was recorded. Please try again.");
        setBotStatus("idle");
        restartHandsFreeSoon();
        return;
      }

      await submitAudioBlob(audioBlob, recordingFormat);
    };

    mediaRecorder.start();
    setIsRecording(true);
    setBotStatus("listening");

    if (mode === "hands-free") {
      attachVad(stream);
    }
  };

  const handleNewChat = async () => {
    stopBotAudio();
    cleanupListening();

    setChats([]);
    setLastUserText("");
    setLastBotReply("");
    setNotice("");
    setLoading(false);
    setIsRecording(false);
    setHandsFreeActive(false);
    setBotStatus("idle");

    try {
      await clearHistory();
    } catch {
      console.log("Could not clear backend history");
    }
  };

  const toggleHandsFree = async () => {
    if (handsFreeActive) {
      setHandsFreeActive(false);
      cleanupListening();
      stopBotAudio();
      return;
    }

    setConversationMode("hands-free");
    setHandsFreeActive(true);
    stopBotAudio();
    await startRecording("hands-free");
  };

  const handleModeChange = async (nextMode) => {
    if (conversationMode === nextMode) return;

    cleanupListening();
    stopBotAudio();
    setConversationMode(nextMode);
    setHandsFreeActive(false);
  };

  const handleVoiceClick = async () => {
    if (conversationMode === "hands-free") {
      await toggleHandsFree();
      return;
    }

    if (botStatus === "speaking") {
      stopBotAudio();
      return;
    }

    stopBotAudio();

    if (!isRecording) {
      await startRecording("manual");
    } else {
      shouldSubmitRecordingRef.current = true;
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setBotStatus("thinking");
    }
  };

  useEffect(
    () => () => {
      cleanupListening();
      stopBotAudio();
    },
    // Cleanup runs only when the app unmounts.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

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

              <div className="mode-toggle" aria-label="Conversation mode">
                <button
                  className={conversationMode === "manual" ? "active" : ""}
                  onClick={() => handleModeChange("manual")}
                  type="button"
                >
                  Manual
                </button>
                <button
                  className={conversationMode === "hands-free" ? "active" : ""}
                  onClick={() => handleModeChange("hands-free")}
                  type="button"
                >
                  Hands-Free
                </button>
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
                aria-label={
                  conversationMode === "hands-free"
                    ? handsFreeActive
                      ? "Stop hands-free conversation"
                      : "Start hands-free conversation"
                    : isRecording
                      ? "Stop recording"
                      : "Start voice chat"
                }
              >
                <span className="voice-orb-core">
                  {conversationMode === "hands-free" && handsFreeActive
                    ? "■"
                    : isRecording
                      ? "■"
                      : "🎙️"}
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
                <p className="eyebrow">
                  {conversationMode === "hands-free"
                    ? handsFreeActive
                      ? "Hands-free session"
                      : "Hands-free ready"
                    : "Voice session"}
                </p>
                <h2>
                  {botStatus === "idle" &&
                    (conversationMode === "hands-free" && !handsFreeActive
                      ? "Start conversation"
                      : "Ready when you are")}
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
