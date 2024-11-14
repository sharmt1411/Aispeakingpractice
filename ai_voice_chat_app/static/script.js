async function sendVoiceMessage(audioBlob) {
    const formData = new FormData();
    formData.append('audio', audioBlob);

    const response = await fetch('/chat/voice_message', {
        method: 'POST',
        body: formData
    });

    const data = await response.json();
    // 播放返回的音频
}
