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
        this._isplaying = false;

        this.port.onmessage = (event) => {
            if (event.data.type === 'audioData') {
                console.log('AudioPlaybackProcessor received audio data');
                this.writeToBuffer(event.data.audioData);
            }
            if (event.data.type === 'setPlaying') {
                this._isplaying = event.data.value;
                console.log('AudioPlayback Processor playing state changed:', event.data.value);
                // if (event.data.value) {     // 每次下发开始，停止播放命令时重置缓冲区
                    this.buffer = new Float32Array(this.bufferSize);
                    this.writePosition = 0;
                    this.readPosition = 0;
                    this.bufferedSamples = 0;
                    console.log('AudioPlaybackProcessor buffer reset');
                // }    
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
        if (this._isplaying) {
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
            } else {
                return true;
            }
            // 不填充，防止破音
            // if (this.bufferedSamples === 0) {
            //     return true;
            // }

            // console.warn('Buffer underflow, filling with zero');
            // const result = new Float32Array(chunkSize);
            // for (let i = 0; i < this.bufferedSamples; i++) {
            //     result[i] = this.buffer[(this.readPosition + i) % this.bufferSize];
            // }
            // for (let i = this.bufferedSamples; i < chunkSize; i++) {
            //     result[i] = 0;
            // }
            // this.readPosition = (this.readPosition + this.bufferedSamples) % this.bufferSize;
            // this.bufferedSamples = 0;
        } else {
            // 停止播放时清空缓冲区
            for (let channel = 0; channel < output.length; channel++) {
                const outputChannel = output[channel];
                outputChannel.fill(0);
            }
            return true;
        }

        return true;
        
    }
}
  
    registerProcessor('audio-playback-processor', AudioPlaybackProcessor);