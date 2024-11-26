from enum import Enum
import threading
import queue
import time
import logging
from typing import Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ServiceState(Enum):
    IDLE = "idle"
    BUSY = "busy"
    DESTROYED = "destroyed"


class ServiceInstance(ABC):
    """
    等待超时后，变为空闲状态，继续等待空闲超时后，自动销毁, 所有状态都需要管理服务进行设置
    主要实现feed方法，以及process_data方法
    feed为数据数据接口，process_data为run(通过start_thread启动线程）中循环执行的方法，默认从队列中获取
    """

    def __init__(self, uid: str, service_name: str, timeout: float, 
                 idle_timeout: float, return_queue: queue.Queue, callback):
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

    def start_thread(self) -> None:
        """输入数据到服务实例"""
        print("parent method: start_thread")
        self.input_data = queue.Queue()  # 清空输入队列
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run)
            self.thread.start()

    def feed(self, data: Any) -> None:  # (user_id, service_name, data)
        """输入数据到服务实例的接口方法"""
        self.input_data.put(data)
        self.last_active_time = time.time()

    def run(self) -> None:
        """运行服务处理逻辑"""
        print(f"Parent Method: Service：Service {self.uid} started.")
        self.state = ServiceState.BUSY
        while not self.stop_event.is_set():
            consecutive_timeout_count = 0
            # user_id, service_name, data = self.input_data.get(block=True, timeout=self.timeout)
            try:
                item = self.input_data.get(block=True, timeout=self.timeout)
                consecutive_timeout_count = 0
            except queue.Empty:
                item = None
                consecutive_timeout_count += 1
            if item is not None:
                try:
                    user_id, service_name, data = item
                    if user_id == "stop":
                        self.stop_event.set()
                        break

                    result = self.process_data(data)
                    self.return_queue.put((user_id, service_name, result))
                except Exception as e:
                    self.return_queue.put((user_id, "message", f"Error: {str(e)}"))
                self.input_data = None
                time.sleep(0.01)
            else:    # 等待超时
                if consecutive_timeout_count >= self.timeout:  # 连续超时30次，销毁
                    try:
                        self.callback(self.uid+'_'+self.service_name, "idle")  # 如果超时，通知管理服务：更新状态，解绑服务，自行准备启动销毁
                        print(f"Service-instance：Service {self.uid} timeout，change to idle.")
                        self.wait_destroy()
                    except Exception as e:
                        print(f"Error: {str(e)}")
                        # 清空队列
                        self.input_data = queue.Queue()
                        self.wait_destroy()
                        continue
        print(f"Service：Service {self.uid} stopped.")

    def wait_destroy(self) -> None:
        """busy状态等待主服务更新状态，先空闲等待再销毁"""
        while self.state != ServiceState.IDLE:
            if time.time() - self.last_active_time > self.idle_timeout + self.timeout:  # active_time是最后一次输入活动时间
                self.destroy()
                return
            time.sleep(0.1)
        wait = time.time()
        # 等待管理服务更新状态后开始计时
        i = 0
        while self.state == ServiceState.IDLE:
            if time.time() - wait > self.idle_timeout:
                self.destroy()
                return
            time.sleep(0.1)
            i += 1
            if i % 30 == 0:
                print(f"Service-instance：Idle Service {self.uid} wait destroy.{i/10}timeout:{self.idle_timeout}")

        if self.state == ServiceState.BUSY:  # 如果还是空闲状态，销毁
            return

    def destroy(self) -> None:
        """idle状态销毁服务实例,通知管理服务更新状态"""
        try:
            print(f"Service-instance：Service {self.uid} callback destroyed.")
            if self.state != ServiceState.DESTROYED:
                self.callback(self.uid+'_'+self.service_name, "destroyed")
            wait = time.time()

            while self.state != ServiceState.DESTROYED:
                if time.time() - wait > 5:
                    print(f"Service-instance：Service {self.uid} timeout destroyed. force stop.")
                    self.state = ServiceState.DESTROYED
                    self.input_data.put(("stop", "stop", "stop"))   # 停止run线程
                    break
                time.sleep(0.1)
        except Exception as e:
            print(f"SI-destroy Error: {str(e)}")
        finally:
            if self.state == ServiceState.DESTROYED:
                self.stop_event.set()
                # if self.thread and self.thread.is_alive():
                #     self.thread.join(timeout=2)
        # self.state = ServiceState.DESTROYED

    @abstractmethod
    def process_data(self, data: Any):
        # 实现具体逻辑
        pass
