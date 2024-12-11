"""
新进程中运行，负责管理各个服务，包括语音识别STT、语音合成TTS，文字处理服务管理器
data输入格式：(user_id, service_name, data)
data输出格式：(user_id, service_name, data)  如果是message，service_name为"message"，则data为字符串
"""

import threading
import queue
import time
from typing import Dict, Optional
import logging
# from abc import ABC, abstractmethod
from services.service_instance import ServiceInstance, ServiceState
from services.speech_to_text import STTService
from services.text_to_speech import TTSService
from services.text_processing import CHATService
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.WARNING)

# service_name: ServiceClass
ServicesClass = {
    "STT": STTService,
    "TTS": TTSService,
    "CHAT": CHATService,
}


class ServiceManagement:
    def __init__(self, input_queue, return_queue, max_instances: int = 6):   # 最大实例数是包含3类服务，需要x3
        self.max_instances = max_instances
        self.instances: Dict[str, ServiceInstance] = {}  # instance_name: ServiceInstance,userid_TTS:instance
        self.input_queue = input_queue  # (user_id, service_name, data)
        self.return_queue = return_queue  # (user_id, service_name, data)
        self.lock = threading.RLock()   # destroy中涉及嵌套调用
        self.thread = None
        self.stop_event = threading.Event()

    def start(self):
        # self.lock = threading.RLock()

        self.thread = threading.Thread(target=self.process_input)
        self.thread.daemon = False  # 设置非守护线程，持续运行
        self.thread.start()
        print("SM：Service manager started.")

    def callback(self, uid, data):
        """用于服务实例返回状态报告的回调函数以及更新状态，列表关系"""

        with self.lock:
            if data == "destroyed":
                self.instances[uid].state = ServiceState.DESTROYED
                instance = self.instances.pop(uid, None)

                print(f"SM-Callback-destroyed: {uid} destroyed.")
                return
            if data == "idle":
                self.instances[uid].state = ServiceState.IDLE
                print(f"SM-Callback-idle: {uid} idled.")
                return

    def process_input(self):
        """发送（userid，service_name，''）启动服务进程"""
        def analyze_data():
            if data == "start" :
                self.return_queue.put((user_id, "message", f"ready{service_name}"))
            else :
                service.feed(item)

        while not self.stop_event.is_set():
            # print("SM：Service manager process input thread running.")
            try:
                item = self.input_queue.get(block=True, timeout=0.5)  # （user_id, service_class, data）
                # print(">>>>>>>>>>>>>>>>>>>>>SM-process_input:", item)
            except queue.Empty:
                continue  # 队列为空，继续等待

            try:
                user_id, service_name, data = item
                # print(f"SM-Input: {user_id}, {service_name}")
                if user_id == "stop":
                    self.shutdown()
                    break
                instance_name = f"{user_id}_{service_name}"
                with self.lock:
                    service = self.instances.get(instance_name, None)
                    if service is not None and service.state == ServiceState.BUSY:
                        # print(f"SM-Instance: {instance_name} exists, feeding data.")
                        analyze_data()
                        continue
                print(f"SM-Instance: {instance_name} not exists, attempting get idle instance.")
                old_name, service = self.get_idle_instance(service_name)
                if service is not None:
                    print(f"SM-Instance:idle instance {old_name} exists, occupying.")
                    self.occupy_instance(instance_name, old_name)
                    analyze_data()

                else:
                    print(f"SM-Instance:No idle instance exists, creating new instance.")
                    service = self.create_instance(user_id, service_name)
                    with self.lock:
                        self.instances[instance_name] = service
                    print(f"SM-Instance: created {instance_name}, starting.")
                    if service is None:
                        self.return_queue.put((user_id, "message", "服务超出最大限制/或者服务调用错误，请等待"))
                        continue
                    print(f"SM-Instance: {instance_name} created, starting inner threads.")
                    # 新建服务实例在内部载入模型完成后，返回准备状态
                    self.instances[instance_name].start_thread()
                    print(f"SM-Instance: {instance_name}  inner threads started")
                    if data == "start":
                        continue
                    service.feed(item)

            except Exception as e:
                print(f"SM-process_input Error: {str(e)}")
                continue

        print("SM：Service manager process input thread stopped.")

    def get_idle_instance(self, service_class):
        """获取空闲的服务实例"""
        with self.lock:
            service_class = ServicesClass.get(service_class, None)
            if service_class is None:
                return None, None
            for name, instance in self.instances.items():
                if isinstance(instance, service_class) and instance.state == ServiceState.IDLE:
                    return name, instance
        return None, None

    def create_instance(self, user_id, service_name, timeout: float = 30.0,
                        idle_timeout: float = 300.0) -> Optional[ServiceInstance]:
        """创建新的服务实例"""
        with self.lock:
            if len(self.instances) >= self.max_instances:
                return None

            # instance_name = f"{user_id}_{service_name}"
            try:
                service_class = ServicesClass.get(service_name, None)
                if service_class is None:
                    print(f"SM-Error: {service_name} is not a valid service name.STT/TTS/CHAT")
                    return None
                instance = service_class(user_id, service_name, timeout, idle_timeout, self.return_queue, self.callback)

                return instance
            except Exception as e:
                print(f"SM-create-instance-Error: {str(e)}")
                return None

    def destroy_instance(self, instance_name: str) -> None:
        """销毁服务实例,并删除字典中的记录，考虑要循环释放，未带锁，由调用自行管理"""
        if instance_name in self.instances:
            instance = self.instances[instance_name]
            instance.state = ServiceState.DESTROYED
            instance.destroy()
            self.instances.pop(instance_name, None)
            print(f"SM-Destroy: {instance_name} destroyed,list popped.")

    def occupy_instance(self, instance_name: str, old_name: str) -> None:
        """占用服务实例"""
        print(f"SM-Occupy: {instance_name} occupying by {old_name}")
        with self.lock:
            print(f"SM-Occupy-lock: {instance_name} occupying by {old_name}")
            if old_name in self.instances:
                self.instances[old_name].state = ServiceState.BUSY
                self.instances[old_name].uid = instance_name.split("_")[0]
                self.instances[instance_name] = self.instances.pop(old_name)
                print(f"SM-Occupy: {instance_name} occupied  {old_name}")

    def release_instance(self, instance_name: str) -> None:
        """释放服务实例"""
        with self.lock:
            if instance_name in self.instances:
                self.instances[instance_name].state = ServiceState.IDLE

    def cleanup_idle_instances(self) -> None:
        """清理空闲实例"""
        with self.lock:
            for name, instance in list(self.instances.items()):
                if instance.state == ServiceState.IDLE:
                    if time.time() - instance.last_active_time > instance.idle_timeout + instance.timeout:
                        self.destroy_instance(name)

    def shutdown(self):
        # self.is_shutting_down = True  # 设置关闭标志
        self.stop_event.set()  # 停止输入队列处理线程，本身带有异常关闭

        # 先停止所有服务
        with self.lock:
            print("SM： Starting shutdown, Stopping all instances.")
            for instance in self.instances.values():
                instance.feed(("stop", "stop", "stop"))
                instance.destroy()                        # 注意死锁
        return len(self.instances) == 0

        # # 等待输入队列处理完成
        # start_time = time.time()
        # while not self.input_queue.empty():
        #     if time.time() - start_time > timeout:
        #         break
        #     time.sleep(0.1)
        #
        # # 停止所有服务实例
        # with self.lock:
        #     for uid, instance in list(self.instances.items()):
        #         try:
        #             # 给实例一定时间完成当前任务
        #             # instance_timeout = min(5.0, timeout / len(self.instances))
        #             self.destroy_instance(uid)
        #         except Exception as e:
        #             print(f"Error shutting down instance {uid}: {e}")
        # self.stop_event.set()


if __name__ == '__main__':
    input_queue = queue.Queue()
    return_queue = queue.Queue()
    sm = ServiceManagement(input_queue, return_queue, max_instances=10)
    sm.start()
    print("SM：Service manager started.")
    input_queue.put(("123", "STT", ""))
    sm.thread.join()
    # print("SM：Service manager stopped.")
