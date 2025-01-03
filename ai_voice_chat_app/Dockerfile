# 选择支持 CUDA 的基础镜像
FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04

# 设置工作目录
WORKDIR /ai_voice_chat_app

# 安装系统依赖（如 Python、pip 等）
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    portaudio19-dev \
    ffmpeg \
    build-essential \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 库
COPY requirements.txt /ai_voice_chat_app/
RUN pip3 install --no-cache-dir -r requirements.txt

RUN pip3 install --no-cache-dir  ctranslate2==4.4.0

# 将 Flask 应用文件复制到容器中
COPY . /ai_voice_chat_app/

# 设置环境变量，告诉 Flask 使用生产模式
ENV FLASK_ENV=production

# 暴露应用运行的端口
EXPOSE 5000

# 启动 Flask 应用
CMD ["python3", "main.py"]