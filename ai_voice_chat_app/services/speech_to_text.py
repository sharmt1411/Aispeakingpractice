import queue
import sys
import os
import threading
import time
import wave
from multiprocessing import current_process
from typing import override, Any

import pyaudio
from RealtimeSTT import AudioToTextRecorder
from .service_instance import ServiceInstance, ServiceState

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.INFO)

if os.name == "nt" and (3, 8) <= sys.version_info < (3, 99):
    from torchaudio._extension.utils import _init_dll_path
    _init_dll_path()

CHUNK = 1024  # Number of audio samples per buffer
FORMAT = pyaudio.paInt16  # Sample format (16-bit integer)
CHANNELS = 1  # Mono audio
RATE = 16000  # Sampling rate in Hz (expected by the recorder)


class STTService(ServiceInstance):
    def __init__(self, uid: str, service_name: str, timeout: float, idle_timeout: float,
                 return_queue: queue.Queue, callback):
        super().__init__(uid, service_name, timeout, idle_timeout, return_queue, callback)

        self.uid = uid  # userid+service_name唯一标识符
        self.service_name = service_name  # 服务名称
        self.timeout = timeout  # 重连超时时间
        self.idle_timeout = idle_timeout  # 空闲等待销毁时间
        self.stop_event = threading.Event()
        self.state = ServiceState.IDLE
        self.return_queue = return_queue
        self.input_data = queue.Queue()  # 每个实例自行维护的队列
        self.thread = None
        self.last_active_time = time.time()
        self.callback = callback
        
        self.recorder = None
        self.full_sentences = []
        self.prev_text = ""
        self.prev_result = ""
        self.prev_stabilize_text = ""
        self.prev_stabilize_count = 0
        self.transcribe_thread = None
        # self.audio_queue = queue.Queue()
        # self.result_queue = result_queue
        # self.session_id = session_id  # 用于区分不同会话

        self.end_of_sentence_detection_pause = 0.45  # 0.45，需要权衡转写时间，等待越长会导致延迟越高
        self.unknown_sentence_detection_pause = 1  # 0.7
        self.mid_sentence_detection_pause = 2.0  # 句子中的停顿，以...结尾的句子，可以适当多等待一会，默认为2

        # 句子断句判断时间，post_speech_silence_duration，超过这个时间的静音才认为是完整句子
        # self.stop_event = threading.Event()

        self.recorder_config = {
            # 'use_extended_logger': True,
            # 'debug_mode': True,
            'no_log_file': True,
            'use_microphone': False,
            'spinner': False,
            'model': 'tiny',  # 'model': 'distil-medium-en, distil-large-v3''large-v2',
            'realtime_model_type': 'small.en',  # 'distil-small.en',  # or tiny.en small.en or distil-small.en or ...
            'language': 'en',
            'silero_sensitivity': 0.2,  # 0.2 0-1，  0最不敏感，需要很大人声才能识别
            'webrtc_sensitivity': 2,  # 3 ranging from 0 (least aggressive / most sensitive) to 3 (most aggressive, least sensitive)
            'post_speech_silence_duration': self.unknown_sentence_detection_pause,
            'min_length_of_recording': 0.8,
            'min_gap_between_recordings': 0,   # 0
            'enable_realtime_transcription': True,
            'realtime_processing_pause': 0.02,  # 0.02 0.1很慢  影响on_realtime_transcription_stabilized的实时转录延迟，越小延迟越低,Specifies the time interval in seconds after a chunk of audio gets transcribed. Lower values will result in more "real-time" (frequent) transcription updates but may increase computational load.
            'on_realtime_transcription_update': None,  # text_detected,  # 每次实时转录有更新时调用
            'on_realtime_transcription_stabilized': self.on_realtime_transcription_stabilized,
            'on_transcription_start': self.on_transcription_start,
            # 整句转录开始触发,可以触发下一步处理逻辑
            'print_transcription_time': True,
            'silero_deactivity_detection': True,
            'silero_use_onnx': True,
            'early_transcription_on_silence': 500,  # 静音检测0.5s后开始整句转录，提前转录工作
            'on_vad_detect_start': None,
            'on_vad_detect_stop': None,
            'beam_size': 3,
            'beam_size_realtime': 3,
            'initial_prompt': (
                "The speaker from China speaks with an accent.End incomplete sentences with ellipses.\n"
                "Examples:\n"
                "Complete: The sky is blue.\n"
                "Incomplete: When the sky...\n"
                "Complete: She walked home.\n"
                "Incomplete: Because he...\n"
            )
        }

    def set_config(self, key, value):
        """设置实时转录配置,重点配置项：
        'use_microphone': False,  # 关闭内置麦克风，使用feed接收音频流，否则不需要调用feed
        具体配置参见上文

        """
        if key in self.recorder_config:
            self.recorder_config[key] = value
            return True
        else:
            return False

    def get_config(self, key):
        if key in self.recorder_config:
            return self.recorder_config[key]
        else:
            return None

    # def set_session_id(self, session_id):
    #     """用于修改会话id，如果连接断开后，有新连接，可以切换到新连接，不用重新初始化"""
    #     self.session_id = session_id
    #     self.full_sentences = []
    #     self.prev_text = ""

    @override
    def start_thread(self) -> None:
        """输入数据到服务实例"""
        print(f"STT服务实例线程start thread：{self.uid}")
        self.input_data = queue.Queue()  # 清空输入队列
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run)
            self.thread.daemon = True  # Ensure the thread doesn't exit prematurely
            self.thread.start()
            self.transcribe_thread = threading.Thread(target=self.transcribe)
            self.transcribe_thread.daemon = True  # Ensure the thread doesn't exit prematurely
            self.transcribe_thread.start()

    @override
    def feed(self, data):
        """输入数据到服务实例的接口方法 内容(user_id, service_name, data)"""
        # print(f"STT服务实例收到数据：{self.uid},{len(data[2])}")
        self.input_data.put(data)
        # print(f"STT服务实例收到数据：{self.uid}，队列长度：{self.input_data.qsize()}")
        self.last_active_time = time.time()

    @override
    def run(self):
        self.state = ServiceState.BUSY
        print(">>>>>>>>>STT-run-current-thread", threading.current_thread().ident, "current-process-id", current_process().ident, flush=True)

        print(f"启动STT服务实例线程：{self.uid}")
        print(f"准备载入whisper模型, {time.time()}")
        if self.recorder is None:
            self.recorder = AudioToTextRecorder(**self.recorder_config)   # 运行时间比较长，需要单独线程运行
        print(f"服务实例，STT模型载入完毕，{self.uid},{time.time()}")
        self.return_queue.put((self.uid, "message", "readySTT"))
        print(f"STT-run-return, {self.uid}, message, readySTT")

        consecutive_silence_count = 0
        while not self.stop_event.is_set():
            # print(f"STT服务实例run循环：{self.uid}")
            try:
                item = self.input_data.get(block=True, timeout=1)
                consecutive_silence_count = 0
            except queue.Empty:
                item = None
                consecutive_silence_count += 1

            if item is not None:
                # print("STTService-RUN-DATA", item)
                try:
                    user_id, service_name, data = item

                    if user_id == "stop" and service_name == "stop":
                        print(f"收到stop,停止STT服务实例线程：{self.uid}")
                        self.stop_event.set()
                        self.recorder.interrupt_stop_event.set()
                        self.recorder.stop_event.set()
                        self.recorder.shutdown()
                        self.transcribe_thread.join(5)
                        print(f"STT服务实例transcribe线程已停止：{self.uid}")
                        return

                    if data:

                        self.process_data(bytearray(data))
                        # self.return_queue.put((user_id, service_name, result))    # 服务特殊由转写线程处理返回
                except Exception as e:
                    print(f"STT-Service run-1 Error: {str(e)}")
                time.sleep(0.01)
            else:
                if consecutive_silence_count % 5 == 0:
                    print(f"STT服务实例线程：{self.uid}空闲等待{consecutive_silence_count}次,超时设置：{self.timeout}")
                if consecutive_silence_count > self.timeout:
                    consecutive_silence_count = 0
                    print(f"！！！！STT服务实例空闲超时，STT服务实例线程：{self.uid}转为空闲")
                    try:
                        self.callback(self.uid+'_'+self.service_name, "idle")  # 如果超时，通知管理服务：更新状态，解绑服务，自行准备启动销毁
                        self.wait_destroy()    # 如果中途被占用，需要继续运行run线程，直到被销毁
                        continue
                    except Exception as e:
                        print(f"STT-Service run Error: {str(e)}")
                        # 清空队列
                        self.input_data = queue.Queue()
                        self.wait_destroy()
                        continue
        print(f"STT服务实例thread线程已停止：{self.uid}")
        self.recorder.shutdown()
        self.transcribe_thread.join(5)
        print(f"STT服务recorder已停止：{self.uid}")

    def process_data(self, data: Any):
        """处理输入数据，返回结果"""
        self.recorder.feed_audio(data, 16000)

    def transcribe(self):
        while not self.stop_event.is_set():
            if self.recorder is None:
                continue
            self.recorder.text(self.on_complete_text)       # 这里是阻塞线程，recorder服务未关闭情况下，会一直卡住等待
            time.sleep(0.01)
        print(f"STT服务实例transcribe线程已停止：{self.uid}")

    def preprocess_text(self, text):
        """去除开头的省略号，空格，并将第一个字母大写"""
        # Remove leading whitespaces
        text = text.lstrip()

        #  Remove starting ellipses if present
        if text.startswith("..."):
            text = text[3:]

        # Remove any leading whitespaces again after ellipses removal
        text = text.lstrip()

        # Uppercase the first letter
        if text:
            text = text[0].upper() + text[1:]

        return text
  
    def on_realtime_transcription_stabilized(self, text):
        """
        在实时转录有稳定更新时调用，保存相关文本（文本为累积的最新段的实时转录），配置分段判断阈值
        同时返回实时结果
        """
        deadlock_count = 3/self.recorder_config['realtime_processing_pause']  # 每0.02转写一次150, 0.1 30
        text = self.preprocess_text(text)
        if self.prev_stabilize_text == text:
            self.prev_stabilize_count += 1
        else:
            self.prev_stabilize_count = 0
        if self.prev_stabilize_count >= deadlock_count:    # 15
            print("！！！实时转录结尾超时！！，中止")
            # self.recorder.interrupt_stop_event.set()  # 停止实时转录
            # self.recorder.frames.clear()
            if self.prev_stabilize_count == deadlock_count:    # 连续10次相同结果，认为是整句结束，并且发送后，后续不再重复放入队列
                self.prev_result = self.prev_text
                self.return_queue.put((self.uid, "STT-result", self.prev_text))       # 解决卡住问题？
                self.input_data.put((self.uid, "TTS", bytearray(22050)))  # 防止输入时提前断开造成数据不完整，转写线程会持续等待数据，导致卡死

            return
        self.prev_stabilize_text = text

        sentence_end_marks = ['.', '!', '?', '。', '！', '？', '……', '...']
        if text.endswith("...") or text.endswith("-"):
            self.recorder.post_speech_silence_duration = self.mid_sentence_detection_pause
        elif text and text[-1] in sentence_end_marks and self.prev_text and self.prev_text[-1] in sentence_end_marks:
            self.recorder.post_speech_silence_duration = self.end_of_sentence_detection_pause
        else:
            self.recorder.post_speech_silence_duration = self.unknown_sentence_detection_pause

        self.prev_text = text

        # If the current text is not a sentence-ending, display it in real-time
        if text:
            self.return_queue.put((self.uid, "STT-realtime", text))
            # self.return_queue.put({"key":"realtime","value":text,"session_id":self.session_id})

            print(f">>>>>>>>>>>>{time.time()}实时转录文本: {text}")

    def on_transcription_start(self):
        """会在认为句子已经完整时，提前调用，可能会被丢弃（如转写完毕时发现不是整句），目前为了速度，暂未考虑这种可能，而是提前转写"""
        print(f">>>>>>>>>>>>>>STT-result:{time.time()}认为是断句，提前开启转录，实时转录结果text: {self.prev_text}")
        self.recorder.post_speech_silence_duration = self.unknown_sentence_detection_pause   # 恢复默认值等待时间
        if self.prev_text == self.prev_result:  # 之前的超时结果已经放入队列，不需要再次转写
            return
        self.return_queue.put((self.uid, "STT-result", self.prev_text))

    def on_complete_text(self, text):
        """会在确定断句并转写完毕后才调用,会创建新线程异步处理整句的转写结果"""
        print(f">>>>>>>>>>>>>>{time.time()}整句转录完毕Received text: {text}")
        self.recorder.post_speech_silence_duration = self.unknown_sentence_detection_pause

        text = self.preprocess_text(text)
        text = text.rstrip()
        if text.endswith("..."):
            text = text[:-2]

        if not text:
            return
        self.return_queue.put((self.uid, "STT-sentence", text))
        # self.return_queue.put({"key":"complete_result","value":text,"session_id":self.session_id})
        self.full_sentences.append(self.prev_text)  # 以实时转录为准
        self.prev_text = ""
        print('\n')
        print('\n')

    def feed_audio_file_thread(self, filepath="output.wav"):
        """需要单声道，16000采样率，采样宽度2（int16）格式音频"""
        if not os.path.exists(filepath):
            if os.path.exists("output.wav"):
                filepath = "output.wav"
            else:
                print("音频文件不存在")
                return
        """Thread function to read audio file data and feed it to the recorder"""
        with wave.open(filepath, 'rb') as wav_file:
            # 获取音频参数
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            frame_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()
            print(f"音频参数: 声道数{n_channels}, 采样宽度{sample_width}, 采样率{frame_rate}, 帧数{n_frames}")
            # 读取音频数据
            frames_to_read = int(frame_rate*0.01)  # 计算需要读取的帧数
            print(f"需要读取的帧数: {frames_to_read}")

            try:
                print("Start feeding now")  # 此时模型已经加载完毕，可以连接
                while not self.stop_event.is_set():
                    # print("start---")
                    audio_data_half_sec = wav_file.readframes(frames_to_read)  # 读取0.5秒的音频数据
                    # print(audio_data_half_sec)
                    # print("读取完成---" )
                    if not audio_data_half_sec:
                        print("录音文件读取结束")
                        time.sleep(6)
                        self.stop_event.set()  # 由于音频断开，导致音频缓冲区没有足够数据，会一直等待并持续转写，因此需要主动停止转写，但需要等待转写进程处理完毕
                        self.recorder.abort()
                        print("停止转写线程")
                        break
                    self.recorder.feed_audio(audio_data_half_sec, 16000)
                    time.sleep(0.01)   # 需要保障模拟实时输入的间隔，否则会超限丢弃
                print("录音全部feed输入结束")
            except Exception as e:
                print(f"feed_audio_thread encountered an error: {e}")
            finally:
                # Clean up the audio stream
                wav_file.close()
                print("Audio stream closed.")

    def feed_audio_thread(self):
        """
        Thread function to read audio data and feed it to the recorder,int16,16000采样率
        """
        try:
            print("ready to receive audio data")
            while not self.stop_event.is_set():
                # Read audio data from the stream (in the expected format)
                data = self.input_data.get()

                # Feed the audio data to the recorder
                self.recorder.feed_audio(data)
        except Exception as e:
            print(f"feed_audio_thread encountered an error: {e}")
        finally:
            # Clean up the audio stream
            print("Audio stream closed.")
            time.sleep(6)  # 等待转写运行完毕
            self.recorder.abort()  # 停止实时转录线程

    def recorder_transcription_thread(self):
        """Thread function to handle transcription and process the text."""
        try:
            while not self.stop_event.is_set():
                self.recorder.text(self.on_complete_text)
        except Exception as e:
            print(f"transcription_thread encountered an error: {e}")
        finally:
            print("Transcription thread exiting.")
            self.stop_event.set()


if __name__ == '__main__':
    # self.recorder.text()会阻塞线程，直到有结果返回，因此需要在新线程中调用,但是实时又不能一次feed太多，会超限丢弃，所以需要分线程操作,并且如果加载文件时需要注意控制sleep时间，避免超限丢弃
    timeout = 10  # 空闲超时时间，单位秒
    idle_timeout = 60  # 空闲超时时间，单位秒
    service_name = "STT"
    return_queue = queue.Queue()
    callback = lambda uid, status: print(f"STT服务实例{uid}状态更新：{status}")

    instance = STTService("test_user", service_name, timeout, idle_timeout, return_queue, callback)
    instance.start_thread()
    # instance.thread.join()

    # recorder = AudioToTextRecorder(**recorder_config)
    # recorder = AudioToTextRecorder(
    #     use_microphone=False,     # Disable built-in microphone usage
    #     spinner=False,             # Disable spinner animation in the console
    #     language="en"          # Set the language to English (default is en-US)
    # )
