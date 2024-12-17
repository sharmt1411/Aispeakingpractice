import os
import sys
import threading
from multiprocessing import current_process


MODEL_NAME = ''
API_KEY = ''
BASE_URL = ''
EMBEDDING_MODEL_NAME = ''
EMBEDDING_API_KEY = ''
EMBEDDING_BASE_URL = ''
EMBEDDING_MODEL_DIMS = 1024
QDRANT_API_KEY = ''
QDRANT_BASE_URL = ''
TTS_ENGINE = ''


current_thread = threading.current_thread()
current_process1 = current_process()
print(">>>>>>>>>>>>>>>>>>>>>>>>>>loading config<<<<<<<<<<<<<<<<<<<<<<<<<")
print(f"当前线程名称: {current_thread.name},id{current_thread.ident}")
print(f"当前进程名称: {current_process1.name},id{current_process1.ident}")


def create_default_config(config_file):
    default_config = """MODEL_NAME = internlm/internlm2_5-20b-chat
API_KEY = your_api_key_here
BASE_URL = https://api.siliconflow.cn/v1

EMBEDDING_MODEL_NAME = BAAI/bge-m3
EMBEDDING_API_KEY = your_embedding_api_key_here_Sk-xxxx
EMBEDDING_BASE_URL = https://api.siliconflow.cn/v1
EMBEDDING_MODEL_DIMS = 1024

QDRANT_API_KEY = your_qdrant_api_key_here
QDRANT_BASE_URL = https://xxxxx.gcp.cloud.qdrant.io

TTS_ENGINE = GTTSEngine

# CHAT模型需要支持openai接口的API，本教程使用InternLM书生浦语大模型进行测试，详见[API申请](https://internlm.intern-ai.org.cn/api/document).也可使用硅基流动平台提供的InternLM20B模型。
# 上边模型用于聊天文本生成，以及记忆获取更新
# 下边模型用于获取用户的embedding向量，用于计算相似度，需要到硅基流动申请API Key，目前大部分嵌入模型免费
# Qdrant用于存储记忆向量，个人用户可免费申请1G，足够记忆使用
# TTS_ENGINE用于语音合成，目前支持的引擎有：SystemEngine,  CoquiEngine, GTTSEngine
"""
    try:
        with open(config_file, 'w', encoding='utf-8') as file:
            file.write(default_config)
        print(f"Created default config file: {config_file}")
    except Exception as e:
        print(f"Error creating file {config_file}: {e}")


def read_config(config_file='config.txt'):
    config = {}
    try:
        with open(config_file, 'r', encoding='utf-8') as file:
            for line in file:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    config[key] = value
        return config
    except FileNotFoundError:
        print(f"Error: {config_file} does not exist.")
        create_default_config(config_file)
        return None
    except Exception as e:
        print(f"Error reading file {config_file}: {e}")
    return None


def load_config():
    global MODEL_NAME, API_KEY, BASE_URL, EMBEDDING_MODEL_NAME, EMBEDDING_API_KEY, EMBEDDING_BASE_URL, EMBEDDING_MODEL_DIMS, QDRANT_API_KEY, QDRANT_BASE_URL, TTS_ENGINE

    if getattr(sys, 'frozen', False) :
        # 如果是打包后的可执行文件
        base_dir = os.path.dirname(sys.executable)
        print(f"Running in frozen mode, base directory: {base_dir}")
    else :
        # 如果是源代码
        base_dir = os.path.dirname(os.path.abspath(__file__))
        print(f"Running in source mode, base directory: {base_dir}")

    config_file = os.path.join(base_dir, 'config.txt')

    config = read_config(config_file)
    if config :
        MODEL_NAME = config.get('MODEL_NAME', 'default_model_name')
        API_KEY = config.get('API_KEY', 'default_api_key')
        BASE_URL = config.get('BASE_URL', 'https://default.url.com')

        EMBEDDING_MODEL_NAME = config.get('EMBEDDING_MODEL_NAME', 'default_embedding_model_name')
        EMBEDDING_API_KEY = config.get('EMBEDDING_API_KEY', 'default_embedding_api_key')
        EMBEDDING_BASE_URL = config.get('EMBEDDING_BASE_URL', 'https://default.embedding.url.com')
        EMBEDDING_MODEL_DIMS = int(config.get('EMBEDDING_MODEL_DIMS', 1024))

        QDRANT_API_KEY = config.get('QDRANT_API_KEY', 'default_qdrant_api_key')
        QDRANT_BASE_URL = config.get('QDRANT_BASE_URL', 'https://default.qdrant.url.com')

        TTS_ENGINE = config.get('TTS_ENGINE', 'SystemEngine')

        print("config初始化成功")
        # print(isinstance(BASE_URL, str))

        print(f"Model Name: {MODEL_NAME}")
        # print(f"API Key: {API_KEY}")
        print(f"Base URL: {BASE_URL}")
    else :
        # 如果config为空，尝试重新读取配置文件
        config = read_config(config_file)
        if config :
            MODEL_NAME = config.get('MODEL_NAME', 'default_model_name')
            API_KEY = config.get('API_KEY', 'default_api_key')
            BASE_URL = config.get('BASE_URL', 'https://default.url.com')

            EMBEDDING_MODEL_NAME = config.get('EMBEDDING_MODEL_NAME', 'default_embedding_model_name')
            EMBEDDING_API_KEY = config.get('EMBEDDING_API_KEY', 'default_embedding_api_key')
            EMBEDDING_BASE_URL = config.get('EMBEDDING_BASE_URL', 'https://default.embedding.url.com')
            EMBEDDING_MODEL_DIMS = int(config.get('EMBEDDING_MODEL_DIMS', 1024))

            QDRANT_API_KEY = config.get('QDRANT_API_KEY', 'default_qdrant_api_key')
            QDRANT_BASE_URL = config.get('QDRANT_BASE_URL', 'https://default.qdrant.url.com')

            TTS_ENGINE = config.get('TTS_ENGINE', 'SystemEngine')

            print("再次初始化变量成功")
            print(f"Model Name: {MODEL_NAME}")
            # print(f"API Key: {API_KEY}")
            print(f"Base URL: {BASE_URL}")
        else :
            print("Failed to read configuration.")
    print(">>>>>>>>>>>>>>>>>>>>>>>>>>config loaded<<<<<<<<<<<<<<<<<<<<<<<<<<")


load_config()
