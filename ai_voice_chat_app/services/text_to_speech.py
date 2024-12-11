import os
import pathlib
import wave
from multiprocessing import current_process
from typing import Any
import asyncio
import re

import queue
import threading
import time

import numpy as np
from RealtimeTTS import TextToAudioStream, SystemEngine, AzureEngine, ElevenlabsEngine, CoquiEngine, GTTSEngine, OpenAIEngine


from .service_instance import ServiceInstance, ServiceState


class TTSService(ServiceInstance):
    """实时文本转语音服务"""
    def __init__(self, uid: str, service_name: str, timeout: float, idle_timeout: float,
                 return_queue: queue.Queue, callback) :
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

        # 以下为实例特殊属性
        self.stream_timeout = 5  # 流式文字超时时间，单位秒
        self.stream_info = None  # 音频流信息
        self.processing = False  # 是否正在处理语音数据
        self.engine = None  # 语音引擎
        self.stream = None  # 语音流对象

    def start_thread(self) -> None:
        """输入数据到服务实例"""
        print(f"TTS服务实例线程start thread：{self.uid}")
        print("current-thread",threading.current_thread())
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"TTS服务实例当前目录：{current_dir}")
            # 选择支持的 engine [SystemEngine(),  CoquiEngine(), GTTSEngine(), OpenAIEngine()]

            self.engine = CoquiEngine(voices_path=os.path.join(current_dir, "coqui_voice"),
                                      local_models_path=os.path.join(current_dir, "models"))
            # self.engine = SystemEngine()  # [SystemEngine(),  CoquiEngine(), GTTSEngine(), OpenAIEngine()]

            voices = self.engine.get_voices()
            print(f"TTS服务实例voices list：{voices}")
            if isinstance(self.engine, CoquiEngine) :
                self.stream_info = [8, 1, 24000]  # 获取音频流信息,宽度值8为int16，8为float32
                voice = "female_arabic"
            else:
                self.stream_info = list(self.engine.get_stream_info())  # 获取音频流信息,宽度值8为int16，8为float32
                voice = voices[1]
            self.engine.set_voice(voice)

            print(f"TTS服务实例音频流信息：{self.stream_info},Voice:{voice}")

            self.stream = TextToAudioStream(self.engine, log_characters=False,
                                         on_text_stream_start=lambda : print(f"text stream started{time.time()}"),
                                         on_audio_stream_start=lambda : print(f"audio stream started{time.time()}"),
                                       )

            self.input_data = queue.Queue()  # 清空输入队列
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self.run)
                self.thread.daemon = False  # Ensure the thread doesn't exit prematurely
                self.thread.start()
        except Exception as e:
            print(f"TTS服务实例初始化错误：{str(e)}")

    def feed(self, data):
        """输入数据到服务实例的接口方法 内容(user_id, service_name, data)"""
        # print(f"TTS服务实例收到数据：{self.uid}")
        self.input_data.put(data)
        # print(f"TTS服务实例收到数据：{self.uid}，队列长度：{self.input_data.qsize()}")
        self.last_active_time = time.time()

    def run(self):
        self.state = ServiceState.BUSY
        print(">>>>>>>>>TTS-run-current-thread", threading.current_thread().ident, "current-process-id", current_process().ident, flush=True)


        print(f"启动TTS服务实例线程：{self.uid}")
        self.return_queue.put((self.uid, "message", "readyTTS"))
        print(f"TTS-run-return, {self.uid}, message, readyTTS")

        consecutive_silence_count = 0
        while not self.stop_event.is_set():
            try:
                item = self.input_data.get(block=True, timeout=1)
                print(f"TTS-Service-RUN-DATA", item)
                consecutive_silence_count = 0
            except queue.Empty:
                item = None
                consecutive_silence_count += 1

            if item is not None:
                # print("TTS-Service-RUN-DATA", item)
                try:
                    user_id, service_name, data = item

                    if user_id == "stop" and service_name == "stop":
                        print(f"收到stop,停止TTS服务实例线程：{self.uid}")
                        self.stop_event.set()
                        print(f"TTS服务实例transcribe线程已停止：{self.uid}")
                        break

                    if data == "begin":
                        self.return_queue.put((self.uid, "TTS-format", self.stream_info))
                        # print(f"TTS服务实例收到音频数据：{self.uid},{len(data)},{type(data)}")
                        self.processing = True
                        self.process_data(data)
                        # 服务特殊由处理线程处理返回
                except Exception as e:
                    print(f"TTS-Service run-1 Error: {str(e)}")
                time.sleep(0.01)
            else:
                if consecutive_silence_count % 5 == 0:
                    print(f"TTS服务实例线程：{self.uid}空闲等待{consecutive_silence_count}次,超时设置：{self.timeout}")
                if consecutive_silence_count > self.timeout:
                    consecutive_silence_count = 0
                    print(f"！！！！TTS服务实例空闲超时，TTS服务实例线程：{self.uid}转为空闲")
                    try:
                        self.callback(self.uid+'_'+self.service_name, "idle")  # 如果超时，通知管理服务：更新状态，解绑服务，自行准备启动销毁
                        self.wait_destroy()    # 如果中途被占用，需要继续运行run线程，直到被销毁
                        continue
                    except Exception as e:
                        print(f"TTS-Service run Error: {str(e)}")
                        # 清空队列
                        self.input_data = queue.Queue()
                        self.wait_destroy()
                        continue
        print(f"TTS服务实例thread线程已停止：{self.uid}")
        self.stream.stop()
        self.engine.shutdown()
        print(f"TTS服务实例线程engine已销毁：{self.uid}")

    def process_data(self, data: Any):
        """处理输入数据，返回结果，调用大模型，小模型，返回结果"""
        generator = self._process_data_group()
        print(f"TTS-Service-process_data-generator started")
        self.stream.feed(generator)
        # print("f2")
        self.stream.play(buffer_threshold_seconds=0,
                         on_sentence_synthesized=lambda sentence : print(f"{sentence}on_sentence_synthesized{time.time()}"),
                         language="en", muted=True,
                         on_audio_chunk= lambda audio_chunk : self.return_queue.put((self.uid, "TTS-result", audio_chunk)))
        # print("f3")
        # stanza需要具体指定语言
        while self.stream.is_playing() :
            # if keyboard.is_pressed("space") :
            #     stream.stop()
            #     break
            time.sleep(0.1)
        print(f"TTS-Service-play ended", time.time())

    def _process_data_group(self) :
        start_time = time.time()
        while self.processing :
            try :
                item = self.input_data.get(timeout=self.stream_timeout)
                print(f"TTS-Service-iterating-data", item)
                start_time = time.time()
                if item[2] == 'end' :
                    self.processing = False
                    break
                yield item[2]  # 具体文字流内容
            except queue.Empty :
                if time.time() - start_time > self.stream_timeout :
                    print("Stream Timeout occurred. Ending data group.")
                    self.processing = False
                    break



if __name__ == '__main__':
    # self.recorder.text()会阻塞线程，直到有结果返回，因此需要在新线程中调用,但是实时又不能一次feed太多，会超限丢弃，所以需要分线程操作,并且如果加载文件时需要注意控制sleep时间，避免超限丢弃
    timeout = 10  # 空闲超时时间，单位秒
    idle_timeout = 60  # 空闲超时时间，单位秒
    service_name = "TTS"
    return_queue = queue.Queue()
    callback = lambda uid, status: print(f"{service_name}服务实例{uid}状态更新：{status}")

    instance = TTSService("test_user", service_name, timeout, idle_timeout, return_queue, callback)
    instance.start_thread()
    instance.feed(("testuid", "TTS", "begin"))
    instance.feed(("testuid", "TTS", "hey!"))
    instance.feed(("testuid", "TTS", "how"))
    instance.feed(("testuid", "TTS", "are"))
    instance.feed(("testuid", "TTS", "you"))
    # instance.feed(("testuid", "TTS", "hey!"))
    # instance.feed(("testuid", "TTS", "how"))
    # instance.feed(("testuid", "TTS", "are"))
    # instance.feed(("testuid", "TTS", "you"))
    # instance.feed(("testuid", "TTS", "hey!"))
    # instance.feed(("testuid", "TTS", "how"))
    # instance.feed(("testuid", "TTS", "are"))
    # instance.feed(("testuid", "TTS", "you"))
    # instance.feed(("testuid", "TTS", "hey!"))
    # instance.feed(("testuid", "TTS", "how"))
    # instance.feed(("testuid", "TTS", "are"))
    # instance.feed(("testuid", "TTS", "you"))
    # instance.feed(("testuid", "TTS", "hey!"))
    # instance.feed(("testuid", "TTS", "how"))
    # instance.feed(("testuid", "TTS", "are"))
    # instance.feed(("testuid", "TTS", "you"))
    # instance.feed(("testuid", "TTS", "end"))
    # time.sleep(10)
    # instance.feed(("testuid", "TTS", "begin"))
    # instance.feed(("testuid", "TTS", "hey!"))
    # instance.feed(("testuid", "TTS", "how"))
    # instance.feed(("testuid", "TTS", "are"))
    # instance.feed(("testuid", "TTS", "you"))
    # instance.feed(("testuid", "TTS", "end"))
    # time.sleep(10)

    # CoquiEngine
    sample_rate = 24000  # 示例采样率
    sample_width = 2  # 示例位深，16位即2字节
    # GTTSEngine
    # sample_rate = 22050  # 示例采样率
    # sample_width = 2  # 示例位深，16位即2字节
    channels = 1  # 示例声道数，立体声为2，单声道为1
    audio_data = None  # 音频数据数组
    while True :
        try :
            audio = return_queue.get(block=True, timeout=10)
            audio_bytes = audio[2]  # 假设音频字节流在元组的第三个位置
            if audio_bytes == "end" or audio_bytes == "begin" or audio_bytes == "readyTTS" or len(audio_bytes) == 3 :   # TTS-formataudio_bytes [8, 1, 22050]
                continue
            print("len",len(audio_bytes),type(audio_bytes))    # coqui 256,GTTS 1024
            # print("audio_bytes",audio_bytes)

            new_data = np.frombuffer(audio_bytes, dtype=np.int16)

            if audio_data is None :
                audio_data = new_data
            else :
                audio_data = np.concatenate((audio_data, new_data))

        except queue.Empty:
            break
        except KeyboardInterrupt :
            instance.stop_event.set()
            break
            # 将字节流转换为NumPy数组

            # 创建WAV文件
    with wave.open('output.wav', 'wb') as wf :
        wf.setnchannels(channels)  # 设置声道数
        wf.setsampwidth(sample_width)  # 设置位深
        wf.setframerate(sample_rate)  # 设置采样率
        wf.writeframes(audio_data.tobytes())  # 写入音频帧

        print("WAV文件已保存，长度:", len(audio_data))
    instance.thread.join()


    # while True:
    #
    #     try:
    #         audio = return_queue.get()
    #
    #         print("len",len(audio[2]))
    #     except queue.Empty:
    #         time.sleep(0.1)
    #     except KeyboardInterrupt:
    #         instance.stop_event.set()
    #         break

    # instance.stop_event.set()
    print("结束")