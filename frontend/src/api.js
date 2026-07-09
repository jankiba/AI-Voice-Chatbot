export const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ||
    `${window.location.protocol}//${window.location.hostname || "127.0.0.1"}:8001`;

export const sendTextMessage = async (message, language = "auto") => {
    const response = await fetch(`${API_BASE_URL}/text-chat`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ message, language }),
    });
    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Text request failed");
    }

    return data;
};

export const sendVoiceMessage = async (audioBlob, language = "auto", filename = "voice.webm") => {
    const formData = new FormData();

    formData.append("file", audioBlob, filename);
    formData.append("language", language);

    const response = await fetch(`${API_BASE_URL}/voice-chat`, {
        method: "POST",
        body: formData,
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
        throw new Error(data.detail || "Voice request failed");
    }

    return data;
};

export const clearHistory = async () => {
    const response = await fetch(`${API_BASE_URL}/clear-history`, {
        method: "DELETE",
    });

    if (!response.ok) {
        throw new Error("Could not clear backend history");
    }
};
