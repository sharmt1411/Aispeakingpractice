class AudioPlaybackProcessor extends AudioWorkletProcessor {
    constructor(options) {
        super();
        const { 
            bufferSeconds = 20, 
            sampleRate = 22050 
        } = options?.processorOptions || {};
        this.bufferSize = bufferSeconds * sampleRate;
        this.buffer = new Float32Array(this.bufferSize);  // 默认 CHUNK_SIZE
        this.writePosition = 0;
        this.readPosition = 0;
        this.bufferedSamples = 0;

        this.port.onmessage = (event) => {
            if (event.data.type === 'audioData') {
            this.writeToBuffer(event.data.audioData);
            }
        };
        console.log('AudioPlaybackProcessor constructor called:', {
            bufferSize: this.bufferSize,
            sampleRate: sampleRate,
            format: '32-bit'
        });
    }
  


  // 添加环形缓冲区写入函数
    writeToBuffer = (newData) => {
        const available = this.bufferSize - this.bufferedSamples;

        if (newData.length > available) {
        console.warn('Buffer overflow, dropping extra data');
        newData = newData.slice(0, available);
        }

        for (let i = 0; i < newData.length; i++) {
        this.buffer[(this.writePosition + i) % this.bufferSize] = newData[i];
        }

        this.writePosition = (this.writePosition + newData.length) % this.bufferSize;
        this.bufferedSamples = Math.min(this.bufferSize, this.bufferedSamples + newData.length);
        
        // 发送缓冲区状态
        this.port.postMessage({
            type: 'bufferStatus',
            writePosition: this.writePosition,
            readPosition: this.readPosition,
            bufferedSamples: this.bufferedSamples
        });
    };

    // 添加环形缓冲区读取函数

    process(inputs, outputs) {
        const output = outputs[0];
        const chunkSize = output[0].length;
        // console.log('Processing chunk of size:', chunkSize);    // 128,由webaudio api决定

        // 从缓冲区读取音频数据
        if (this.bufferedSamples >= chunkSize) {
            for (let channel = 0; channel < output.length; channel++) {
            const outputChannel = output[channel];
            for (let i = 0; i < chunkSize; i++) {
                outputChannel[i] = this.buffer[(this.readPosition + i) % this.bufferSize];
            }
            }
    
            // 更新读取位置
            this.readPosition = (this.readPosition + chunkSize) % this.buffer.length;
            this.bufferedSamples -= chunkSize;
    
            return true;
        }
        if (this.bufferedSamples === 0) {
            return true;
        }

        console.warn('Buffer underflow, filling with zero');
        const result = new Float32Array(chunkSize);
        for (let i = 0; i < this.bufferedSamples; i++) {
            result[i] = this.buffer[(this.readPosition + i) % this.bufferSize];
        }
        for (let i = this.bufferedSamples; i < chunkSize; i++) {
            result[i] = 0;
        }
        this.readPosition = (this.readPosition + this.bufferedSamples) % this.bufferSize;
        this.bufferedSamples = 0;
        return true;
        
        }
    }
  
    registerProcessor('audio-playback-processor', AudioPlaybackProcessor);