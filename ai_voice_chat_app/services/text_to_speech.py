from services import ServiceInstance
from typing import Any


class TTSService(ServiceInstance):
    def process_data(self, data: Any) -> Any:
        # 实现语音转文本的具体逻辑
        return f"STT processed: {data}"
