import React, { useState, useEffect, useRef, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import './App.css';

// 录音音频配置
const AUDIO_CONFIG = {
  sampleRate: 16000,
  channelCount: 1,
  bitsPerSample: 16
};

// 创建socket实例
const socket = io('http://localhost:5000', {
  transports: ['websocket'],
  reconnectionAttempts: Infinity,
  reconnectionDelay: 1000,
  timeout: 20000,
  forceNew: true,
  path: '/socket.io/',
  upgrade: false,
  autoConnect: false
});

function App() {
  const [messages, setMessages] = useState<string[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isReadyToTalk, setIsReadyToTalk] = useState(false);
  // message 显示区域
  const [statusMessage, setStatusMessage] = useState('');
  // 当前语音输入的文本
  const [currentText, setCurrentText] = useState(''); 
  // 当前LLM回复的文本
  const [chatResponse, setChatResponse] = useState('');
  // 当前LLM回复的建议
  const [chatGuidance, setChatGuidance] = useState('');

  const isRecordingRef = useRef(false);
  const isReadyToTalkRef = useRef(false);
  const lastTextRef = useRef('');
  const audioContextRef = useRef<AudioContext | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioWorkletNodeRef = useRef<AudioWorkletNode | null>(null);
  const userId = useRef<string>("test-user-1");
  const audioFormatRef = useRef<AudioFormat | null>(null);  // 存储音频格式信息

  const sampleRateRef = useRef<number>(22050);   // 返回音频采样率

  // 添加环形缓冲区相关状态
  const BUFFER_SIZE = 22050 * 20; // 固定缓冲区大小：22050Hz * 20秒
  const CHUNK_SIZE = 512; // 每次处理的采样点数
  // const circularBufferRef = useRef<Float32Array>(new Float32Array(BUFFER_SIZE));
  const writePositionRef = useRef<number>(0);
  const readPositionRef = useRef<number>(0);
  const bufferedSamplesRef = useRef<number>(0);

  

  // 初始化录音（麦克风）音频上下文和处理器
  const initAudioContext = useCallback(async () => {
    console.log('Initializing audio context...', {
      existing: {
        audioContext: !!audioContextRef.current,
        workletNode: !!workletNodeRef.current,
        stream: !!streamRef.current
      }
    });

    // 如果已经初始化过，就不再重复初始化
    if (audioContextRef.current?.state === 'running' && workletNodeRef.current) {
      console.log('Recorder Audio context already initialized and running');
      return;
    }

    try {
      // 创建新的 AudioContext
      if (!audioContextRef.current) {
        audioContextRef.current = new AudioContext({
          sampleRate: AUDIO_CONFIG.sampleRate
        });
        console.log('Created new AudioContext');
      }

      // 加载并注册 AudioWorklet
      try {
        console.log('Loading AudioWorklet module...');
        await audioContextRef.current.audioWorklet.addModule('/audioProcessor.js');
        console.log('Recoder AudioWorklet module loaded successfully');
      } catch (error) {
        console.error('Failed to load AudioWorklet module:', error);
        throw error;
      }

      // 获取麦克风权限
      if (!streamRef.current) {
        console.log('Requesting microphone access...');
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            channelCount: AUDIO_CONFIG.channelCount,
            sampleRate: AUDIO_CONFIG.sampleRate
          }
        });
        streamRef.current = stream;
        console.log('Microphone access granted');
      }

      // 创建和连接音频节点
      if (!workletNodeRef.current) {
        console.log('Creating AudioWorkletNode...');
        const source = audioContextRef.current.createMediaStreamSource(streamRef.current);
        const workletNode = new AudioWorkletNode(audioContextRef.current, 'audio-processor', {
          numberOfInputs: 1,
          numberOfOutputs: 1,
          channelCount: AUDIO_CONFIG.channelCount,
          processorOptions: {
            sampleRate: AUDIO_CONFIG.sampleRate
          }
        });

        // 连接音频节点
        console.log('Connecting audio nodes...');
        source.connect(workletNode);
        // workletNode.connect(audioContextRef.current.destination); //不需要连接
        workletNodeRef.current = workletNode;
        console.log('Audio nodes connected successfully');

        // 设置 录音workletNode 的消息处理，接收audio-processor 发送的数据
        workletNode.port.onmessage = (event) => {
          const { type, data, format } = event.data;
          
          if (type === 'audioData' && isRecordingRef.current && isReadyToTalkRef.current && socket.connected) {
            try {
              socket.emit('audio_stream', {
                user_id: userId.current,
                data: Array.from(data),  // 已经是字节数组
                format: {
                  sampleRate: AUDIO_CONFIG.sampleRate,
                  channels: 1,
                  bitDepth: 16,
                  bufferSize: 1024
                },
                timestamp: new Date().toISOString()
              });
            } catch (error) {
              console.error('Error sending audio data:', error);
            }
          }
        };
      }

      // 确保音频上下文处于运行状态
      if (audioContextRef.current.state === 'suspended') {
        console.log('Resuming suspended audio context...');
        await audioContextRef.current.resume();
        console.log('Audio context resumed');
      }

      console.log('Audio initialization completed successfully', {
        contextState: audioContextRef.current.state,
        hasWorkletNode: !!workletNodeRef.current,
        hasStream: !!streamRef.current
      });

    } catch (error) {
      console.error('Error in audio initialization:', error);
      // 清理资源
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      if (audioContextRef.current) {
        await audioContextRef.current.close();
        audioContextRef.current = null;
      }
      workletNodeRef.current = null;
      throw error;
    }
  }, []);

  const initplaybackContext = useCallback(async (format: AudioFormat) => {
    // 当TTS-format 收到时，playbackContext为空或者采样率不同时，创建新的AudioContext
    if (playbackContextRef.current) {
      playbackContextRef.current.close();
    }
    playbackContextRef.current = new AudioContext({
      sampleRate: format.rate
    });
    console.log('Created new playback AudioContext:', {
      sampleRate: playbackContextRef.current.sampleRate,
      state: playbackContextRef.current.state,
      baseLatency: playbackContextRef.current.baseLatency,
      outputLatency: playbackContextRef.current.outputLatency
    });

    try {
      // 加载 AudioWorklet 模块
      await playbackContextRef.current.audioWorklet.addModule('/audioPlaybackProcessor.js');
  
      // 创建 AudioWorkletNode
      const workletNode = new AudioWorkletNode(
        playbackContextRef.current, 
        'audio-playback-processor', {
          processorOptions: { 
            bufferSeconds: 20, 
            sampleRate: format.rate,
          }   
        }
      );

      workletNode.port.onmessage = (event) => {
        if (event.data.type === 'bufferStatus') {
          // 更新本地缓冲区状态
          writePositionRef.current = event.data.writePosition;
          readPositionRef.current = event.data.readPosition;
          bufferedSamplesRef.current = event.data.bufferedSamples;
        }
      };
  
      // 连接到音频输出
      workletNode.connect(playbackContextRef.current.destination);
  
      // 存储 WorkletNode 引用
      audioWorkletNodeRef.current = workletNode;
  
      console.log('Playback AudioWorklet initialized successfully', {
        sampleRate: playbackContextRef.current.sampleRate,
        state: playbackContextRef.current.state
      });
  
    } catch (error) {
      console.error('Failed to initialize AudioWorklet:', error);
      if (playbackContextRef.current) {
        playbackContextRef.current.close();
        playbackContextRef.current = null;
      }
      if (audioWorkletNodeRef.current) {
        audioWorkletNodeRef.current.port.close();
        audioWorkletNodeRef.current = null;
      }
      throw error;
    }

  }, []);


  // 连接WebSocket
  const connectSocket = useCallback(() => {
    console.log('Attempting to connect...');
    if (!socket.connected) {
      socket.connect();
    }
  }, []);

  // 开始注册流程的函数
  const startRegistration = useCallback(() => {
    console.log('Starting registration process...');
    if (!isConnected) {
      console.log('Not connected, first connecting...');
      connectSocket();
    } else {
      console.log('Sending registration with user ID:', userId.current);
      socket.emit('register', { user_id: userId.current });
    }
  }, [isConnected, connectSocket]);

  // 监听录音状态变化，发送给audio-processor 同步
  useEffect(() => {
    if (workletNodeRef.current) {
      console.log('Sending recording state to AudioWorklet:', isRecordingRef.current);
      workletNodeRef.current.port.postMessage({
        type: 'setRecording',
        value: isRecordingRef.current
      });
    }
  }, [isRecording]);

  // Socket 连接管理
  useEffect(() => {
    console.log('WebSocket connection status:', socket.connected);
    let reconnectTimer: NodeJS.Timeout;
    let isInitialConnection = true;

    const handleConnect = () => {
      console.log('Connected to WebSocket');
      setIsConnected(true);
      setConnectionError('');
      if (isInitialConnection) {
        console.log('Initial connection, sending registration');
        socket.emit('register', { user_id: userId.current });
        isInitialConnection = false;
      }
    };

    const handleDisconnect = () => {
      console.log('Disconnected from WebSocket');
      setIsConnected(false);
      setIsReadyToTalk(false);
      // 尝试重新连接
      reconnectTimer = setTimeout(() => {
        console.log('Attempting to reconnect...');
        socket.connect();
      }, 2000);
    };

    const handleConnectError = (error: Error) => {
      console.error('Connection error:', error);
      setConnectionError('连接失败');
    };

    const handleMessage = (message: string) => {
      console.log('Received message:', message);
      
      if (message === 'readySTT') {
        console.log('Ready to receive STT-realtime data');
        setIsReadyToTalk(true);
        isReadyToTalkRef.current = true;
        initAudioContext().catch(error => {
          console.error('Failed to initialize audio:', error);
          setIsReadyToTalk(false);
          isReadyToTalkRef.current = false;
        });
      }
      setStatusMessage(message);
    };

    const handleSTT = (data: any) => {
      // console.log('Received STT-realtime data:', data);
      // 检查数据格式并提取文本
      const text = typeof data === 'string' ? data : data.text;
      
      if (text && text !== lastTextRef.current) {
        lastTextRef.current = text;  // 更新上一次的文本
        setCurrentText(text);        // 更新当前显示的文本
        // console.log('Updated display text:', text);
      }
    };

    const handleChatResponse = (data: string) => {
      console.log('Received CHAT-response:', data);
      
      if (data === 'begin') {
        console.log('Clearing chat response area');
        setChatResponse('');
      } else {
        setChatResponse(prev => prev + data);
        // console.log('Updated chat response:', data);
      }
    };

    const handleChatGuidance = (data: string) => {
      console.log('Received CHAT-guidance:', data);
      setChatGuidance(data);
    };

    const handleTTSFormat = (format: number[]) => {
      console.log('>>>>>>>>Received TTS-format:', format);
      // 解析 pyaudio 格式映射
      // 8 = paInt16, 1 = paFloat32
      const width = format[0] === 8 ? 16 : (format[0] === 1 ? 32 : format[0]);
      audioFormatRef.current = {
        width,  // 转换 pyaudio 格式到实际位宽
        channels: format[1],
        rate: format[2]
      };
      console.log('Parsed audio format:', audioFormatRef.current);
      if (audioFormatRef.current.rate !== sampleRateRef.current) {
        sampleRateRef.current = audioFormatRef.current.rate;
        // initCircularBuffer(sampleRateRef.current);
        // 确保播放 AudioContext 使用正确的采样率
      }
      if (!playbackContextRef.current || playbackContextRef.current.sampleRate !== audioFormatRef.current.rate) {
        initplaybackContext(audioFormatRef.current);
      }
    };

    const handleTTSResult = (data: any) => {
      // console.log('Received TTS-result audio data');
      // 确保数据是 ArrayBuffer
      let audioData;
      if (data instanceof Uint8Array) {
        audioData = data;
      } else if (typeof data === 'string') {
        // 如果是 base64 字符串，先解码
        const binary = atob(data);
        audioData = new Uint8Array(binary.length);
        for (let i = 0; i < binary.length; i++) {
          audioData[i] = binary.charCodeAt(i);
        }
      } else if (data instanceof ArrayBuffer) {
        audioData = new Uint8Array(data);
      } else if (Array.isArray(data)) {
        // 如果是字节数组，转换为 Uint8Array
        audioData = new Uint8Array(data);
      } else {
        console.error('Unsupported data format:', typeof data);
        return;
      }
      // 打印前几个字节用于调试
      // console.log('First few bytes:', Array.from(audioData.slice(0, 16)));
      placeAudioChunk(audioData);
    };

    // 注册事件监听器
    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    socket.on('connect_error', handleConnectError);
    socket.on('message', handleMessage);
    socket.on('STT-realtime', handleSTT);
    socket.on('CHAT-response', handleChatResponse);
    socket.on('CHAT-guidance', handleChatGuidance);
    socket.on('TTS-format', handleTTSFormat);
    socket.on('TTS-result', handleTTSResult);

    // 如果 socket 未连接，尝试连接
    if (!socket.connected) {
      console.log('Socket not connected, attempting to connect...');
      socket.connect();
    }

    // 清理函数
    return () => {
      console.log('Cleaning up socket connections...');
      clearTimeout(reconnectTimer);
      socket.off('connect', handleConnect);
      socket.off('disconnect', handleDisconnect);
      socket.off('connect_error', handleConnectError);
      socket.off('message', handleMessage);
      socket.off('STT-realtime', handleSTT);
      socket.off('CHAT-response', handleChatResponse);
      socket.off('CHAT-guidance', handleChatGuidance);
      socket.off('TTS-format', handleTTSFormat);
      socket.off('TTS-result', handleTTSResult);
      
      // 清理 AudioContext
      if (audioContextRef.current) {
        audioContextRef.current.close();
      }
      if (playbackContextRef.current) {
        playbackContextRef.current.close();
      }
      socket.disconnect();
    };
  }, [connectSocket, initAudioContext, initplaybackContext]); // connectSocket, initAudioContext]);

  // 音频状态管理
  useEffect(() => {
    if (!isReadyToTalkRef.current && audioContextRef.current) {
      console.log('Not ready to talk, cleaning up audio resources...');
      if (workletNodeRef.current) {
        workletNodeRef.current.disconnect();
        workletNodeRef.current = null;
      }
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop());
        streamRef.current = null;
      }
      if (audioContextRef.current?.state !== 'closed') {
        audioContextRef.current.close().catch(console.error);
        audioContextRef.current = null;
      }
    }
  }, [isReadyToTalk]);

  // 录音控制函数
  const toggleRecording = async () => {
    try {
      if (!isReadyToTalk) {
        console.log('Not ready to talk yet');
        return;
      }

      const newRecordingState = !isRecordingRef.current;
      console.log('Toggling isrecording state to:', newRecordingState);
      
      if (newRecordingState) {
        // 开始录音前确保音频上下文已初始化
        if (!audioContextRef.current || !workletNodeRef.current) {
          console.log('Initializing audio before recording...');
          await initAudioContext();
        }
        startRegistration();
      }
      // if (!newRecordingState){                 //在useEffect[isRecording]中已经处理
      //   if (workletNodeRef.current) {
      //     workletNodeRef.current.port.postMessage({
      //       type: 'setRecording',
      //       value: false
      //     });
      //   }
      // }

      // 更新状态
      setIsRecording(newRecordingState);
      isRecordingRef.current = newRecordingState;  // 触发状态变化

      // 通知 AudioWorklet
      // if (workletNodeRef.current) {
      //   console.log('Sending recording state to AudioWorklet:', newRecordingState);
      //   workletNodeRef.current.port.postMessage({
      //     type: 'setRecording',
      //     value: newRecordingState
      //   });
      // }

      // 发送录音状态到服务器
      // if (socket.connected) {
      //   socket.emit('recording_state', {
      //     user_id: userId.current,
      //     is_recording: newRecordingState
      //   });
      // }
    } catch (error) {
      console.error('Error toggling recording:', error);
      setIsRecording(false);
      isRecordingRef.current = false;
    }
  };

  // 音频播放函数,放入环形缓冲区
  const placeAudioChunk = async (audioData: Uint8Array) => {
    try {
      if (!audioFormatRef.current) {
        console.error('Audio format not received yet');
        return;
      }
      const { width, channels, rate } = audioFormatRef.current;

      // 根据格式将字节数据转换为 Float32Array
      let buffer: Float32Array;
      if (width === 16) { // paInt16
        buffer = new Float32Array(audioData.length / 2);
        const dataView = new DataView(audioData.buffer);
        
        for (let i = 0; i < buffer.length; i++) {
          const sample = dataView.getInt16(i * 2, true);
          buffer[i] = sample / 32768.0;
        }
      } else if (width === 32) { // paFloat32
        const dataView = new DataView(audioData.buffer);
        buffer = new Float32Array(audioData.length / 4);
        for (let i = 0; i < buffer.length; i++) {
          buffer[i] = dataView.getFloat32(i * 4, true);
        }
      } else {
        console.error('Unsupported audio format width:', width);
        return;
      }

      // 写入环形缓冲区   coqui生成块128，int16长度
      // writeToBuffer(buffer);
      audioWorkletNodeRef.current?.port.postMessage({
        type: 'audioData', 
        audioData: buffer
      });
      // console.log("writeToBuffer,writePosition:", writePositionRef.current, "readPosition:", readPositionRef.current, "bufferedSamples:", bufferedSamplesRef.current);

    } catch (error) {
      console.error('Error in playAudioChunk:', error);
    }
  };

  // 修改清理函数
  useEffect(() => {
    return () => {
      if (audioWorkletNodeRef.current) {
        audioWorkletNodeRef.current.disconnect();
        audioWorkletNodeRef.current = null;
      }
      if (audioContextRef.current) {
        audioContextRef.current.close();
        audioContextRef.current = null;
      }
      if (playbackContextRef.current) {
        playbackContextRef.current.close();
        playbackContextRef.current = null;
      }
      writePositionRef.current = 0;
      readPositionRef.current = 0;
      bufferedSamplesRef.current = 0;
      // circularBufferRef.current.fill(0);
    };
  }, []);

  // 添加音频格式配置接口
  interface AudioFormat {
    width: number;
    channels: number;
    rate: number;
  }

  return (
    <div className="app">
      <div className="container">
        {/* 状态指示器 */}
        <div className="status-wrapper">
          <div className={`connection-indicator ${isConnected ? 'connected' : ''}`}>
            <span className="status-dot"></span>
            <span className="status-text">
              {isConnected ? '已连接' : '未连接'}
            </span>
          </div>
          {connectionError && (
            <div className="error-toast">{connectionError}</div>
          )}
        </div>
  
        {/* 语音识别显示区 */}
        <div className="recognition-card">
          <div className="card-content fade-in">
            {currentText || '等待语音输入...'}
          </div>
        </div>
  
        {/* AI响应区域 */}
        <div className="response-card">
          <div className="card-content slide-up">
            {chatResponse || '等待 AI 响应...'}
          </div>
        </div>
  
        {/* 指引信息区 */}
        <div className="guidance-card">
          <div className="card-content fade-in">
            {chatGuidance || '等待指引...'}
          </div>
        </div>
  
        {/* 语音控制区 */}
        <div className="control-section">
          <button
            className={`voice-control-button ${isRecording ? 'recording' : ''}`}
            onClick={toggleRecording}
            disabled={!isReadyToTalk}
          >
            <span className="button-icon"></span>
            <span className="button-text">
              {isRecording ? '停止录音' : '开始录音'}
            </span>
          </button>
          {statusMessage && (
            <div className="status-message slide-up">{statusMessage}</div>
          )}
        </div>
      </div>
    </div>
  );
  
}

export default App;
