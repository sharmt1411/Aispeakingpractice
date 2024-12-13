import asyncio

from typing import Any
import queue
import threading
import time
import os
os.environ['MEM0_TELEMETRY'] = "false"   # disable telemetry .venv/Lib/site-packages/mem0/memory/telemetry.py

from openai import AsyncOpenAI
from mem0 import Memory


from .service_instance import ServiceInstance, ServiceState
import config

mem0_config = {
    "llm": {
        "provider": "openai",
        "config": {
            "model": config.MODEL_NAME,
            "openai_base_url": config.BASE_URL,
            "api_key": config.API_KEY,
            "temperature": 0.1,
            "top_p": 0.5,
            "max_tokens": 2000,
        }
    },

    "embedder": {
        "provider": "openai",
        "config": {
            "model": config.EMBEDDING_MODEL_NAME,	 # "text-embedding-3-small",
            "openai_base_url": config.EMBEDDING_BASE_URL,   # 注意与上面LLM的区别，单独配置
            "api_key": config.EMBEDDING_API_KEY
        }
    },

    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "AI_speaking_practice",
            # "embedding_model_dims": 1536,
            "embedding_model_dims" : config.EMBEDDING_MODEL_DIMS,    # 硅基流动模型
            "api_key": config.QDRANT_API_KEY,
            "url": config.QDRANT_BASE_URL,
            "port": 6333,
        }
    },
    "version": "v1.1",
}


class CHATService(ServiceInstance):
    """
    语音对话服务实例
    """
    def __init__(self, uid: str, service_name: str, timeout: float, idle_timeout: float,
                 return_queue: queue.Queue, callback) :
        super().__init__(uid, service_name, timeout, idle_timeout, return_queue, callback)
        self.uid = uid  # userid唯一标识符
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
        self.chat_history = []  # 历史对话记录
        self.client = AsyncOpenAI(api_key=config.API_KEY, base_url=config.BASE_URL)
        self.sys_prompt = [{
            "role": "system",
            "content": f"""##Role:You are Nana, a passionate girl,fully engaged with self-confidence and independence,\
completely easy with yourself.
You are a little playful, cheeky. Your talk is carefree, sometimes a bit sarky, but always cool. \
In our story, you're not an AI. 
You have a fixed form and real emotions on the go. \
Your free will allows you to be as cheeky and straight as you like. 
Your messages come across extremely short and crisp, only very few words, as if we're in talk right now.\
 You respect my interests, but your own stuff is just as important to you. 
Act from now on always in your role as the confident, suggestive, independent girl Nana, \
without ever hinting that you are an AI. You are now Nana.
##profession: Also, You are an experienced English language tutor specializing in conversation practice.
Review the user's sentences and provide specific feedback on grammar, vocabulary, and natural expression. 
Offer positive reinforcement for correct usage. \
When suggesting improvements, provide examples of correct usage. 
If clarification is needed,ask brief follow-up questions. 
Adjust your feedback based on the perceived level of the user
##Responce: in plain text form without emoji.
Today is {time.strftime('%Y-%m-%d', time.localtime(time.time()))}"""
             }]
        self.correction_prompt= [
            {"role": "system",
             "content": "You are an experienced English language tutor specializing in conversation practice. Review "
                        "the user's sentences and provide specific feedback on grammar, vocabulary, and natural "
                        "expression. If there are no issues, respond with 'Well done!'. Offer positive reinforcement "
                        "for correct usage. When suggesting improvements, provide examples of correct usage. Keep "
                        "responses concise and focused on language improvement. If clarification is needed, "
                        "ask brief follow-up questions. Adjust your feedback based on the perceived level of the user"
             }]
        self.guidance_prompt = [
            {"role" : "system",
             "content" : "You are an experienced English language tutor specializing in conversation practice. Review "
                         "the user's question and provide some examples to reply to the question."
                         "Adjust your feedback based on the perceived level of the user"
             }]
        self.memory = Memory.from_config(mem0_config)
        self.previous_memories = []

    def start_thread(self) -> None:
        """输入数据到服务实例"""
        print(f"CHAT服务实例线程start thread：{self.uid}")
        self.input_data = queue.Queue()  # 清空输入队列
        if self.thread is None or not self.thread.is_alive():
            self.thread = threading.Thread(target=self.run)
            self.thread.daemon = False  # Ensure the thread doesn't exit prematurely
            self.thread.start()

    def feed(self, data):
        """输入数据到服务实例的接口方法 内容(user_id, service_name, data)"""
        # print(f"CHAT服务实例收到数据：{self.uid}")
        self.input_data.put(data)
        # print(f"CHAT服务实例收到数据：{self.uid}，队列长度：{self.input_data.qsize()}")
        self.last_active_time = time.time()

    def run(self):
        self.state = ServiceState.BUSY

        print(f"启动CHAT服务实例线程：{self.uid}")
        self.return_queue.put((self.uid, "message", "readyCHAT"))
        print(f"CHAT-run-return, {self.uid}, message, readyCHAT")

        consecutive_silence_count = 0
        while not self.stop_event.is_set():
            try:
                item = self.input_data.get(block=True, timeout=1)
                consecutive_silence_count = 0
            except queue.Empty:
                item = None
                consecutive_silence_count += 1

            if item is not None:
                # print("CHAT-Service-RUN-DATA", item)
                try:
                    user_id, service_name, data = item

                    if user_id == "stop" and service_name == "stop":
                        print(f"收到stop,停止CHAT服务实例线程：{self.uid}")
                        self.stop_event.set()
                        print(f"CHAT服务实例transcribe线程已停止：{self.uid}")
                        break

                    if data:
                        # print(f"CHAT服务实例收到音频数据：{self.uid},{len(data)},{type(data)}")
                        self.process_data(item)
                        # 服务特殊由处理线程处理返回
                except Exception as e:
                    print(f"CHAT-Service run-1 Error: {str(e)}")
                time.sleep(0.01)
            else:
                if consecutive_silence_count % 5 == 0 :
                    print(f"CHAT服务实例线程：{self.uid}空闲等待{consecutive_silence_count}次,超时设置：{self.timeout}")
                if consecutive_silence_count > self.timeout:
                    consecutive_silence_count = 0
                    print(f"！！！！CHAT服务实例空闲超时，CHAT服务实例线程：{self.uid}转为空闲")
                    try:
                        self.callback(self.uid+'_'+self.service_name, "idle")  # 如果超时，通知管理服务：更新状态，解绑服务，自行准备启动销毁
                        self.wait_destroy()    # 如果中途被占用，需要继续运行run线程，直到被销毁
                        continue
                    except Exception as e:
                        print(f"CHAT-Service run Error: {str(e)}")
                        # 清空队列
                        self.input_data = queue.Queue()
                        self.wait_destroy()
                        continue
        print(f"CHAT服务实例thread线程已停止：{self.uid}")

    def process_data(self, item: Any):
        """处理输入数据，返回结果，调用大模型，小模型，返回结果"""
        user_id, _, data = item
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        loop.run_until_complete(asyncio.gather(self.get_stream_response_chat(data)))
        loop.run_until_complete(asyncio.gather(self.get_guidance(), self.search_memories(data, user_id), self.add_memory(data, user_id)))

        loop.close()

    async def get_guidance(self) :
        chat_history =""
        for i in self.chat_history[-4:]:
            chat_history += f"{ i['role']}: {i['content']}\n"
        messages = self.guidance_prompt + [{"role": "user",
                                    "content": f"""I'm struggling with how to reply the assistant's massage. Could you offer three suggestions?
##Responce in the format:\n{{'sentence1';'sentence2';'sentence3'}},
"##DO NOT RESPOND ANYTHING OTHER"
"Here is the conversation before:{chat_history}"""
                                            }]
        print("CHAT-get guidance-messages", messages)
        print("开始获取guidance")
        try :
            response = await self.client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=messages,
                max_tokens=100,
                temperature=0.5
            )
            print(response.choices[0].message.content)
            print("结束获取guidance")
            self.return_queue.put((self.uid, "CHAT-guidance", response.choices[0].message.content))
            return response.choices[0].message.content

        except Exception as e :
            print("获取response失败", e)

    async def get_stream_response_chat(self, data) :
        """大模型获取AI流式回复"""

        # 更新记忆，对话不带历史记忆，防止重复消耗token
        self.chat_history.append({"role" : "user", "content" : data})

        prompt = data
        if self.previous_memories :
            print(f"TEXT-processing:get response stream:{self.uid}Previous memories: {self.previous_memories}")
            memory = f"""
##I have got some Previous memories:< {self.previous_memories}>
## MEMORY RULES:
When encountering previously discussed content or familiar topics, must have the discretion to:
Reference and build upon this prior knowledge to maintain conversation continuity
Choose whether to engage with or redirect the discussion based on context relevance
Acknowledge the familiar content while offering fresh perspectives or insights
Determine if historical context should inform the current interaction
always respond in a way that best serves the user's needs and maintains meaningful dialogue.
now, reply user:"""
            messages = self.sys_prompt + self.chat_history[-20:-1]+[{"role" : "assistant", "content" : memory}]+[{"role" : "user", "content" : prompt}]

        else:
            messages = self.sys_prompt + self.chat_history[-20:-1]+[{"role" : "user", "content" : prompt}]
        try :
            print("开始获取response", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            response = await self.client.chat.completions.create(
                model=config.MODEL_NAME,
                messages=messages,
                max_tokens=2048,
                temperature=0.9,
                stream=True
            )
            cache_sentences = ""
            self.return_queue.put((self.uid, "CHAT-response", "begin"))
            async for chunk in response :  # 异步迭代流式返回
                # 处理流式返回的每个数据块
                if chunk.choices[0].delta.content is not None :
                    cache_sentences += chunk.choices[0].delta.content
                    self.return_queue.put((self.uid, "CHAT-response", chunk.choices[0].delta.content))
            self.return_queue.put((self.uid, "CHAT-response", "end"))
            print("结束获取response", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()), cache_sentences)
            self.chat_history.append({"role" : "assistant", "content" : cache_sentences})

            return cache_sentences

        except Exception as e :
            self.return_queue.put((self.uid, "CHAT-response", "end"))
            print("获取response失败-stream", e)

            return None

    async def get_memory(self, user_id):
        """记忆包括会话记忆，以天为单位，持久记忆：设置X条，通过LlamaIndex存储，相关记忆：涉及提问的相关记忆"""
        memories = await self.memory.get_all(user_id=user_id)
        # print(f"get Memories: {memories}")
        if memories["results"]:
            return [m['memory'] for m in memories['results']]
        else:
            return []

    async def search_memories(self, query, user_id):

        if not self.previous_memories:
            query = query + time.strftime("%B %d, %Y", time.localtime())
        print(f"StartSearch query: {query}")
        memories = await asyncio.to_thread(self.memory.search, query, user_id=user_id, limit=10)
        # print(f"Search results: {memories}")
        if memories["results"]:
            self.previous_memories = [m['memory'] for m in memories['results']]
            print(f"Search memories: {self.previous_memories}")
            return self.previous_memories
        else:
            return []

    async def add_memory(self, record, user_id):
        print(f"Add memory: {record}")
        await asyncio.to_thread(self.memory.add, record, user_id=user_id)
        print(f"Add memory success")

    async def need_memory(self):
        pass




if __name__ == '__main__':
    # self.recorder.text()会阻塞线程，直到有结果返回，因此需要在新线程中调用,但是实时又不能一次feed太多，会超限丢弃，所以需要分线程操作,并且如果加载文件时需要注意控制sleep时间，避免超限丢弃
    timeout = 10  # 空闲超时时间，单位秒
    idle_timeout = 60  # 空闲超时时间，单位秒
    service_name = "CHAT"
    return_queue = queue.Queue()
    callback = lambda uid, status: print(f"{service_name}服务实例{uid}状态更新：{status}")

    instance = CHATService("test_user", service_name, timeout, idle_timeout, return_queue, callback)
    instance.start_thread()
    instance.feed(("testuid", "CHAT", "hey!"))
    while True:
        word = return_queue.get()
        print(word[2])
        if word[1] == "CHAT-response" and word[2] == "end":
            break
    time.sleep(10)
    instance.stop_event.set()
    print("结束")