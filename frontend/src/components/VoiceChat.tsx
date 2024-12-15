import React, { useState, useRef, useEffect, useCallback } from 'react';
import { PhoneCall, PhoneIcon } from 'lucide-react';
import AudioVisualizer from './AudioVisualizer';
import ChatMessage from './ChatMessage';
import SuggestedReply from './SuggestedReply';
import { io, Socket } from 'socket.io-client';

// 录音音频配置
const AUDIO_CONFIG = {
  sampleRate: 16000,
  channelCount: 1,
  bitsPerSample: 16
};

// 创建socket实例
const socket = io(window.location.origin, {
// const socket = io('http://localhost:5000', {  
  transports: ['websocket'],
  reconnectionAttempts: Infinity,
  reconnectionDelay: 1000,
  timeout: 20000,
  forceNew: true,
  path: '/socket.io/',
  upgrade: false,
  autoConnect: false
});

const VoiceChat: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    { id: 1, text: "Hey! How can I assist you today?", sender: "other" },
  ]);
 
  const [isRecording, setIsRecording] = useState(false);   // 录音状态
  const [isCalling, setIsCalling] = useState(false);  //拨号状态
  const [isReadyToTalk, setIsReadyToTalk] = useState(false);
  
  const [amplitude, setAmplitude] = useState<Uint8Array>(new Uint8Array());   //设置录音动态变化


  // message 显示区域
  const [statusMessage, setStatusMessage] = useState('');
  const [chatGuidance, setChatGuidance] = useState(['遇到不认识的单词，可以直接拼写字母',
    '不直到怎么聊，可以试试照着这里读','语音识别不准，可能是发音有问题，可以针对强化~']);

  const isConnectedRef = useRef(false);
  const isRecordingRef = useRef(false);     // 录音状态
  const isCallingRef = useRef(false);
  const isReadyToTalkRef = useRef(false);
  const isReadyTTSRef = useRef(false);
  const isReadySTTRef = useRef(false);
  const countAmplitude = useRef(0);


  const lastTextRef = useRef('');
  const audioContextRef = useRef<AudioContext | null>(null);
  const playbackContextRef = useRef<AudioContext | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const workletNodeRef = useRef<AudioWorkletNode | null>(null);
  const audioWorkletNodeRef = useRef<AudioWorkletNode | null>(null);   // 音频播放节点
  const userId = useRef<string>("test-user-1");
  const audioFormatRef = useRef<AudioFormat | null>(null);  // 存储音频格式信息
  const isPlayingRef = { current: false };  // 拨号音乐是否播放

  const sampleRateRef = useRef<number>(22050);   // 返回音频采样率
  const phoneCallRef = useRef<HTMLAudioElement | null>(null);  // 拨号音乐
  const buttonbounceRef = useRef(false)    // 按钮抖动
  // 添加环形缓冲区相关状态

  const writePositionRef = useRef<number>(0);
  const readPositionRef = useRef<number>(0);
  const bufferedSamplesRef = useRef<number>(0);

  

  // 初始化录音（麦克风）音频上下文和处理器
  const initAudioContext = useCallback(async () => {
    console.log('Initializing audio context...', new Date().toISOString() ,{
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
          
          if (type === 'audioData' && isCallingRef.current && isReadyToTalkRef.current && socket.connected) {
            try {
              socket.emit('audio_stream', {
                user_id: userId.current,
                data: data,//Array.from(data),  // 已经是字节数组 uint8array，此处序列化json对象，可以直接传输二进制
                format: {
                  sampleRate: AUDIO_CONFIG.sampleRate,
                  channels: 1,
                  bitDepth: 16,
                  bufferSize: 1024
                },
                timestamp: new Date().toISOString()
              });
              if (countAmplitude.current % 5 === 0) {
                setAmplitude(data);
              }
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

      console.log('Audio initialization completed successfully', new Date().toISOString() ,{
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
    console.log('IPb-Initializing playback context...')
    if (playbackContextRef.current && playbackContextRef.current.sampleRate !== format.rate) {
      console.log('IPB-Sample rate mismatch, Closing existing playback AudioContext...');
      playbackContextRef.current.close();
    }
    if (playbackContextRef.current && playbackContextRef.current.sampleRate === format.rate)  {
      console.log('IPB-Playback AudioContext already initialized and running,return');
      console.log('IPB-Playback AudioContext state:', playbackContextRef.current.state);
      if (playbackContextRef.current.state === 'suspended') {
        console.log('IPB-Resuming suspended playback AudioContext...');
        await playbackContextRef.current.resume();
        console.log('IPB-Playback AudioContext resumed');
      }
      return;   // 后台播放节点，已经统一按照float32格式单声道传入，只是采样率可能变化
    }
    playbackContextRef.current = new AudioContext({
      sampleRate: format.rate
    });
    console.log('IPB-Created new playback AudioContext:', {
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
  
      console.log('IPB-Playback AudioWorklet initialized successfully', {
        sampleRate: playbackContextRef.current.sampleRate,
        state: playbackContextRef.current.state
      });
  
    } catch (error) {
      console.error('IPB-Failed to initialize AudioWorklet:', error);
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


  const playphoneCall = useCallback(() => {
    // 使用静态变量追踪是否已经播放
    console.log('playphoneCall-Playing phone call...');
    try {
      // 如果已经在播放，直接返回
      if (isPlayingRef.current) {
        console.log('playphoneCall-Phone call is already playing');
        return Promise.resolve();
      }
  
      if (phoneCallRef.current) {
        console.log('playphoneCall-Stopping previous phone call...');
        phoneCallRef.current.pause();
        phoneCallRef.current.currentTime = 0;
      }
  
      phoneCallRef.current = new Audio('dialsound.mp3');
      
      return new Promise<void>((resolve, reject) => {
        // 确保 phoneCallRef.current 非空
        if (!phoneCallRef.current) {
          reject(new Error('playphoneCall-Failed to create audio object'));
          return;
        }
        console.log('playphoneCall-phoneCallRef.current:', phoneCallRef.current);
        // 标记已经开始播放
        isPlayingRef.current = true;
  
        let stopTimer: NodeJS.Timeout;
        const audioContext = new AudioContext();
        const source = audioContext.createMediaElementSource(phoneCallRef.current);
        const gainNode = audioContext.createGain();
        
        source.connect(gainNode);
        gainNode.connect(audioContext.destination);
  
        // 渐进式淡出函数
        const fadeOut = (duration = 1000) => {
          console.log('playphoneCall-Fading out...');
          if (!phoneCallRef.current) {
            isPlayingRef.current = false;
            resolve(); 
            return;
          }
  
          const startTime = audioContext.currentTime;
          gainNode.gain.setValueAtTime(1, startTime);
          gainNode.gain.linearRampToValueAtTime(0, startTime + duration / 1000);
  
          setTimeout(() => {
            if (phoneCallRef.current) {
              phoneCallRef.current.pause();
              phoneCallRef.current.currentTime = 0;
            }
            // 重置播放状态
            isPlayingRef.current = false;
            resolve();
          }, duration);
        };
        
        const checkReadyToTalk = () => {
          console.log('playphoneCall-Checking if ready to talk...');
          clearTimeout(stopTimer);
          if (!isCallingRef.current) {
            console.log('playphoneCall-Not calling, stopping...');
            if (phoneCallRef.current) {
              phoneCallRef.current.pause();
              phoneCallRef.current.currentTime = 0;
            }
            isPlayingRef.current = false;
            resolve();
            return;
          }
          if ((isRecordingRef.current && phoneCallRef.current)) {
            clearTimeout(stopTimer);
            console.log('playphoneCall-Ready to talk, starting fade out...');
            fadeOut(); // 使用渐进式淡出
          } else {
            // 如果还未就绪，继续检查
            console.log('playphoneCall-Not ready to talk, checking again...');
            stopTimer = setTimeout(checkReadyToTalk, 500);
          }
        };

        console.log('playphoneCall-Phone call starting to play through...');
        if (phoneCallRef.current) {
          phoneCallRef.current.play()
            .then(() => {
              // 开始监听 isReadyToTalk 状态
              stopTimer = setTimeout(checkReadyToTalk, 500);
            })
            .catch(error => {
              // 播放失败时重置状态
              isPlayingRef.current = false;
              reject(error);
            });
        }
         
  
        // phoneCallRef.current.oncanplaythrough = () => {
        //   console.log('playphoneCall-Phone call can play through...');
        //   if (phoneCallRef.current) {
        //     phoneCallRef.current.play()
        //       .then(() => {
        //         // 开始监听 isReadyToTalk 状态
        //         stopTimer = setTimeout(checkReadyToTalk, 500);
        //       })
        //       .catch(error => {
        //         // 播放失败时重置状态
        //         isPlayingRef.current = false;
        //         reject(error);
        //       });
        //   }
        // };
  
        phoneCallRef.current.onerror = (error) => {
          // 错误时重置状态
          isPlayingRef.current = false;
          reject(error);
        };
      });
    } catch (error) {
      console.error('Failed to load phone call audio:', error);
      return Promise.reject(error);
    }
  }, []);


  // 连接WebSocket
  const connectSocket = useCallback(() => {
    console.log('Attempting to connect...');
    if (!socket.connected) {
      socket.connect();
      console.log('Connected successfully');
    }
  }, []);


  // 开始注册流程的函数
  const startRegistration = useCallback(() => {
    console.log('Starting registration process...');
    if (!isConnectedRef.current) {
      console.log('Not connected, first connecting...');
      connectSocket();
    } else {
      console.log('Sending registration with user ID:', userId.current);
      socket.emit('register', { user_id: userId.current });
    }
  }, []);    


  // 监听录音状态变化，发送给audio-processor 同步,并且控制播放
  useEffect(() => {
    console.log('isRecording State cahnged, isRecordingRef.current:', isRecordingRef.current, 'isRecording:', isRecording);
    
    if (workletNodeRef.current) {
      console.log('Sending recording state to recorderAudioWorklet:', isRecordingRef.current);
      workletNodeRef.current.port.postMessage({
        type: 'setRecording',
        value: isRecordingRef.current
      });
    }
    if (audioWorkletNodeRef.current) {
      console.log('Stoprecording,Sending setplaying message to playbackAudioWorklet', isRecordingRef.current);
      audioWorkletNodeRef.current?.port.postMessage({
        type: 'setPlaying',
        value: isRecordingRef.current
      });
      // playbackContextRef.current?.suspend();
      // console.log("playbackContext state suspended", playbackContextRef.current?.state);

    }
  }, [isRecording]);


  // 准备好后开始录音
  useEffect(() => {
    if (isReadyToTalkRef.current && isCallingRef.current) { 
      console.log('>>>>UE-isreadytotalk and isCalling, prepare to change isRecording to true...');
      if (workletNodeRef.current) {
        setTimeout(() => {
          if (workletNodeRef.current) {
            setStatusMessage('Ready');
            setIsRecording(true);
            isRecordingRef.current = true;
          }
        }, 5000);
        
        // setStatusMessage('Ready');
        // setIsRecording(true);
        // isRecordingRef.current = true;
        
        // if(!isInitialConnection.current) {
        //   console.log('None Initializing call, auto recording');
        //   setIsRecording(true);
        //   isRecordingRef.current = true;
        // } else {
        //   console.log('Initializing call, no auto recording');
        //   // isInitialConnection.current = false;
        // }
        // 由播放逻辑中侦听实现
        // if (phoneCallRef.current) {
        //   phoneCallRef.current.pause();
        //   phoneCallRef.current.currentTime = 0;
        // }
        
      }
    } else {
      console.log('isRecording conditions not met, isReadyToTalkRef.current:', isReadyToTalkRef.current, "useEffect");
      isRecordingRef.current = false;
      setIsRecording(false);
    }
  }, [isReadyToTalk, isCalling]);


  // Socket 连接管理
  useEffect(() => {
    console.log('WebSocket connection status:', socket.connected);
    let reconnectTimer: NodeJS.Timeout;
    let isInitialConnection = true;

    const handleConnect = () => {
      console.log('Connected to WebSocket');
      isConnectedRef.current = true;
      if (isInitialConnection) {
        console.log('Initial connection, sending registration');
        socket.emit('register', { user_id: userId.current });
        isInitialConnection = false;
      }
    };

    const handleDisconnect = () => {
      console.log('Disconnected from WebSocket');
      isConnectedRef.current = false;
      setIsReadyToTalk(false);
      isReadyToTalkRef.current = false;
      // 尝试重新连接
      reconnectTimer = setTimeout(() => {
        console.log('Attempting to reconnect...');
        socket.connect();
      }, 2000);
    };

    const handleConnectError = (error: Error) => {
      console.error('Connection error:', error);
    };

    const handleMessage = (message: string) => {
      console.log('Received message:', message);
      
      if (message === 'readySTT') {
        // console.log('Ready to receive STT-realtime data');
        isReadySTTRef.current = true;
        if (isReadyTTSRef.current) {
          console.log('Ready to talk, init AudioContext',new Date().toISOString());
          
          setIsReadyToTalk(true);
          isReadyToTalkRef.current = true;
          initAudioContext().catch(error => {
            console.error('Failed to initialize audio:', error);
            setIsReadyToTalk(false);
            isReadyToTalkRef.current = false;
          });
          if (audioFormatRef.current) {
            initplaybackContext(audioFormatRef.current).catch(error => {
              console.error('Failed to initialize playback audio:', error);
              setIsReadyToTalk(false);
              isReadyToTalkRef.current = false;
            });
          }
          // console.log('Ready to talk',new Date().toISOString());
        }
      }
          

      if (message === 'readyTTS') {
        // console.log('Ready to receive TTS data');
        isReadyTTSRef.current = true;
        if (isReadySTTRef.current) {
          console.log('Ready to talk, init AudioContext', new Date().toISOString());
          setIsReadyToTalk(true);
          isReadyToTalkRef.current = true;
          initAudioContext().catch(error => {
            console.error('Failed to initialize audio:', error);
            setIsReadyToTalk(false);
            isReadyToTalkRef.current = false;
          });
          if (audioFormatRef.current) {
            initplaybackContext(audioFormatRef.current).catch(error => {
              console.error('Failed to initialize playback audio:', error);
              setIsReadyToTalk(false);
              isReadyToTalkRef.current = false;
            });
          }
          // console.log('Ready to talk', new Date().toISOString());
        }
      }

      if (message === 'start loading model...')
        message = 'Calling Nana...';
      setStatusMessage(message);
    };

    // 处理录音的实时语音转文本,用户输入
    const handleSTTRealtime = (data: any) => {
      // console.log('Received STT-realtime data:', data);
      // 检查数据格式并提取文本
      const text = typeof data === 'string' ? data : data.text;
      // 分为更新，和新建聊天气泡
      if (text && text !== lastTextRef.current) {
        if (lastTextRef.current !== '') {
          lastTextRef.current = text
          setMessages((prevMessages) => {
            return prevMessages.map((msg, index) => 
              index === prevMessages.length - 1 
                ? { ...msg, text: text, sender: 'user' }
                : msg
            );
          });
        } else if (text) {
          lastTextRef.current = text;  // 新增聊天气泡
          setMessages((prevMessages) => [...prevMessages, { id: prevMessages.length + 1, 
            text: text, sender: 'user' }]);        // 更新当前显示的文本
        }
      }
    };

    const handleSTTSentence = (data: any) => {
      console.log('Received STT-sentence data:', data);
      // 检查数据格式并提取文本
      const text = typeof data === 'string' ? data : data.text;
      
      if (text) {
        lastTextRef.current = '';  // 更新上一次的文本
        // setMessages((prevMessages) => {
        //   return prevMessages.map((msg, index) => 
        //     (index === prevMessages.length - 1 && msg.sender === 'user')
        //       ? { ...msg, text: text, sender: 'user' }
        //       : msg
        //   );
        // });
      }
    };

    const handleChatResponse = (data: string) => {
      // console.log('Received CHAT-response:', data);
      
      if (data === 'begin') {
        console.log('Chat responce Assistant begin saying something...');
        setMessages((prevMessages) => [...prevMessages, { id: prevMessages.length + 1, 
          text: '', sender: 'other' }]);        // 更新当前显示的文本
        return
      } 
      if (data === 'end') {
        return
      }
      setMessages((prevMessages) => {
        return prevMessages.map((msg, index) => 
          (index === prevMessages.length - 1 && msg.sender === 'other')
            ? { ...msg, text: msg.text + data, sender: 'other' }
            : msg
        );
      });
      // console.log('Updated chat response:', data);
      
    };

    const handleChatGuidance = (data: string) => {
      console.log('Received CHAT-guidance:', data);
      try {
        const guidanceReg = /\{(.*?)\}/;  // 添加 s 标志，允许 . 匹配换行符
        const match = data.match(guidanceReg);
        if (match) {
          const content = match[1];
          const guidanceList = content.split(';').map(item => 
            item.trim().replace(/^'|'$/g, '') // 去除首尾单引号
          );
          setChatGuidance(guidanceList);
        }
      } catch (error) {
        console.error('Error in chat guidance update:', error);
      }
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
      if (isCallingRef.current) {
        placeAudioChunk(audioData);
      }
    };

    // 注册事件监听器
    socket.on('connect', handleConnect);
    socket.on('disconnect', handleDisconnect);
    socket.on('connect_error', handleConnectError);
    socket.on('message', handleMessage);
    socket.on('STT-realtime', handleSTTRealtime);
    socket.on('STT-sentence', handleSTTSentence);
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
      socket.off('STT-realtime', handleSTTRealtime);
      socket.off('STT-sentence', handleSTTSentence);
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


  // 录音控制函数
  const toggleRecording = async () => {
    if (buttonbounceRef.current) {
      return;
    }
    
    try {
      buttonbounceRef.current = true;
      const newCallingState = !isCallingRef.current;
      console.log('>>>Toggling recording...', newCallingState);
      // isInitialConnection.current = false;  
      // 点击后取消对isrecording更新后不能自动打开录音的限制，
      // 原来是防止网页加载后长时间不操作，isreadytalk后自动打开录音
      
      if (newCallingState) {

        console.log('Initializing 2audiocontext before recording...');
        initAudioContext();
        playbackContextRef?.current?.resume();     // 需用户点击交互后才能启动，其他函数无法启动
        
        isCallingRef.current = newCallingState
        setIsCalling(isCallingRef.current);
        
        // 要开始录音,先播放拨号音频
        // if (!isReadyToTalkRef.current) {  // 未准备好先注册启动服务
        console.log('>>>>>>start registration...');
        setStatusMessage('Calling Nana...');
        playphoneCall();      // 在isreadytotalk状态设置后停止
        startRegistration();
        // } 

      } else {
        // 停止录音
        isReadyToTalkRef.current = false;
        setIsReadyToTalk(false);
        isReadySTTRef.current = false;
        isReadyTTSRef.current = false;
        isCallingRef.current = false;
        setIsCalling(false);
        setStatusMessage('Disconnect');
      }


    } catch (error) {
      console.error('Error toggling recording:', error);
      setIsRecording(false);
      isRecordingRef.current = false;
    } finally {
      buttonbounceRef.current = false;
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
      audioWorkletNodeRef.current?.port.postMessage({
        type: 'audioData', 
        audioData: buffer
      });

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
      if (phoneCallRef.current) {
        phoneCallRef.current.pause();
        phoneCallRef.current = null;
      }
      isPlayingRef.current = false;

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


  interface Message {
    id: number;
    text: string;
    sender: 'user' | 'other';
  }


  const chatContainerRef = useRef<HTMLDivElement>(null);
  


  useEffect(() => {
    if (chatContainerRef.current) {
      chatContainerRef.current.scrollTop = chatContainerRef.current.scrollHeight;
    }
  }, [messages]);



  return (
    <div className="w-full max-w-md bg-black/30 backdrop-blur-md rounded-xl overflow-hidden flex flex-col h-[700px]">
      {/* 状态栏 - 绝对定位在右上角 */}
      <div
        className={`absolute top-2 right-2 z-10 ${isReadyToTalk ? 'bg-green-500' : 'bg-red-500'} text-white/70 px-3 py-1 rounded-full text-xs`}
      >
        {isReadyToTalk ? 'Ready' : statusMessage}
        </div>
      
      <div 
        ref={chatContainerRef}
        className="flex-1 overflow-y-auto p-6 scrollbar-thin scrollbar-thumb-white/20 scrollbar-track-transparent"
      >
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            message={message.text}
            sender={message.sender as 'user' | 'other'}
          />
        ))}
      </div>

      <div className="bg-gray/40 p-4 space-y-2">
        <p className="text-white/60 text-xs font-medium mb-2 ml-1">YOU CAN SAY</p>
        <div className="grid grid-cols-1 gap-2">
          {chatGuidance.map((reply, index) => (
            <SuggestedReply
              key={index}
              message={reply}
              // onSelect={() => {
              //   setMessages([...messages, { id: messages.length + 1, text: reply, sender: 'user' }]);
              // }}
            />
          ))}
        </div>

        <div className="flex justify-center mt-6 relative">
          {isRecording && <AudioVisualizer isActive={isRecording} Amplitude={amplitude} />}

          <button
            className={`relative p-4 rounded-full transition-colors duration-300  ${
              isCalling ? 'bg-red-500 hover:bg-red-600 animate-button-pulse' : 'bg-green-500 hover:bg-green-600'
            }`}
            onClick={toggleRecording}
            // disabled={!isReadyToTalk}
          >
            {isCalling ? (
              <PhoneCall className="w-6 h-6 text-white relative z-10" />
            ) : (
              <PhoneIcon className="w-6 h-6 text-white relative z-10" />
            )}
            
          </button>
          
        </div>
      </div>
     
    </div>
    
    
  );
};

export default VoiceChat;