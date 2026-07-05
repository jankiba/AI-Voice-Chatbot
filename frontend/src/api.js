import axios from "axios";

const API_BASE_URL = "http://127.0.0.1:8000";

export const sendTextMessage = async (message) => {
    const response = await axios.post(`${API_BASE_URL}/text-chat`, {
        message,
    });
    return response.data;
};

export const sendVoiceMessage = async (audioBlob) => {
    const formData = new FormData();
    formData.append("file", audioBlob, "voice.webm");

    const response = await axios.post(`${API_BASE_URL}/voice-chat`, formData, {
        headers: {
            "Content-Type": "multipart/form-data",
        },
    });

    return response.data;
};