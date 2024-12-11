console.log('AudioProcessor.js loaded');
// 处理页面录音逻辑
class AudioProcessor extends AudioWorkletProcessor {
    constructor(options) {
        super();
        this._isRecording = false;
        this._sampleCount = 0;
        this._bufferSize = 1024; // 设置缓冲区大小，1024点
        this._buffer = new Float32Array(this._bufferSize);
        this.sampleRate = options?.processorOptions?.sampleRate || 16000;
        
        console.log('Recorder AudioProcessor constructor called:', {
            sampleRate: this.sampleRate,
            isRecording: this._isRecording,
            bufferSize: this._bufferSize,
            format: '16-bit mono'
        });
        
        // 处理setRecording消息，True为开始，False为结束，直接初始化缓冲区
        this.port.onmessage = (event) => {
            const { type, value } = event.data;
            console.log('Recorder AudioProcessor received message:', { type, value });
            
            if (type === 'setRecording') {
                const oldState = this._isRecording;
                this._isRecording = value;
                console.log('Recorder AudioProcessor recording state changed:', {
                    from: oldState,
                    to: this._isRecording
                });
                
                if (this._isRecording) {
                    this._sampleCount = 0;
                    this._buffer = new Float32Array(this._bufferSize);
                }
            }
        };
    }

    process(inputs, outputs, parameters) {
        const input = inputs[0];
        if (!input || !input[0]) {
            return true;
        }

        const inputChannel = input[0];

        if (this._isRecording) {
            // 将新的样本添加到缓冲区
            for (let i = 0; i < inputChannel.length && this._sampleCount < this._bufferSize; i++) {
                this._buffer[this._sampleCount++] = inputChannel[i];
            }

            // 当缓冲区满时，处理并发送数据
            if (this._sampleCount >= this._bufferSize) {
                try {
                    // 转换为16位整数数组
                    const audioData = new Int16Array(this._bufferSize);
                    for (let i = 0; i < this._bufferSize; i++) {
                        // 将Float32 [-1,1] 转换为 Int16 [-32768,32767]
                        const sample = Math.max(-1, Math.min(1, this._buffer[i]));
                        audioData[i] = sample < 0 ? sample * 0x8000 : sample * 0x7FFF;
                    }

                    // 转换为字节数组
                    const byteArray = new Uint8Array(audioData.buffer);
                    
                    this.port.postMessage({
                        type: 'audioData',
                        data: byteArray,
                        format: {
                            sampleRate: this.sampleRate,
                            channels: 1,
                            bitDepth: 16,
                            bufferSize: this._bufferSize
                        }
                    });

                    // 重置缓冲区
                    this._sampleCount = 0;
                    this._buffer = new Float32Array(this._bufferSize);
                } catch (error) {
                    console.error('AudioProcessor error:', error);
                }
            }
        }

        return true;
    }
}

try {
    registerProcessor('audio-processor', AudioProcessor);
    console.log('Recorder AudioProcessor registered with config:', {
        bufferSize: 1024,
        sampleRate: sampleRate,    
        format: '16-bit mono'
    });
} catch (error) {
    console.error('Failed to register AudioProcessor:', error);
}
