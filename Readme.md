## AI-English-Tutor

<img width="667" alt="image" src="https://github.com/user-attachments/assets/3b4e44d9-758e-4739-8fbb-b161fc1709fa">


### Introduction

As Chinese people, most of us, including myself, even though we can read English, our pronunciation is extremely inaccurate.

We often have "mute English" - we can read but can't speak.

Traditionally, English speaking practice relied on foreign teachers or English corners, but most people couldn't participate due to various reasons like time and money costs.

Most importantly, as introverted people who rarely speak in general, how could we possibly find someone to practice speaking with?

Therefore, an AI English tutor naturally solves part of these problems.

I named her Nana, taken from the mobile assistant in "100 Things" - it's a very pleasant name.


### Features

The project mainly integrates functionalities from several famous repositories, including:

- Speech Recognition: [RealtimeSTT](https://github.com/KoljaB/RealtimeSTT), using faster whisper model for near real-time speech recognition.
- Text-to-Speech: [RealtimeTTS](https://github.com/KoljaB/RealtimeTTS), using various TTS engines like GTTS, Coqui models for text-to-speech conversion.
- Text Dialogue: Using [mem0](https://github.com/mem0ai/mem0)-based memory dialogue technology to achieve accurate conversation history recall, avoiding complex implementation of context storage.


### How to Use

- First, you need to have Python environment installed.
- Then, download the project code and install related dependencies.
- install cuda and pytorch,see in [GPU Support with CUDA](#gpu-support-with-cuda)
- if you don't have GPU, you can use CPU version.And use TTS engine like GTTS。
- And then, run ai_voice_chat_app/main.py file,the first time you run it, it will generate a config file named config.txt, you need to fill in.
- AND finally,run the main.py file again, open browser and enter http://localhost:5000/ to access the homepage.
- After running, fill in the related configurations in ai_voice_chat_app/config.txt, most can be applied for free.
- Then you can happily chat with Nana~ (First run requires downloading about 2G of models, please wait patiently)
- Note: The project can also be deployed on servers for multi-user conversations. However, currently the original STT library Coqui model hasn't implemented parallelization, so one user needs about 4G VRAM using Coqui.
  - A 24G VRAM server can support about 5-6 users chatting simultaneously.
  - After server deployment, service instances will be automatically allocated and destroyed after 300s, or can run long-term on your own machine.


### Project Structure

- ai_voice_chat_app/ Main project directory
  - app.py Main program
  - config.txt Configuration file
  - main.py Startup file
  - static/ Static files directory
    - react Frontend build directory
  - websocket/ WS service directory
  - services/ Speech recognition and text-to-speech services directory
    - coqui_voice/ Voice cloning audio files
    - models/ Speech recognition model files
    - service_management Service management file
    - services_instance.py Service instance and logic definition file
    - Other service files
- fronted/ Frontend project directory
- requirements.txt Dependencies file


### flowchart
![流程图](https://github.com/user-attachments/assets/43ff042c-c839-4e5c-b77b-67d500ef8221)


### some questions 
- use Linux
  - you may need run
    ```
    sudo apt-get update
    sudo apt-get install python3-dev
    sudo apt-get install portaudio19-dev
    ```
  - Linux these libraries can be installed with pip. `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*` to install    
  - Note that LD_LIBRARY_PATH must be set before launching Python. run
    ```
    export LD_LIBRARY_PATH=`python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'`
    ```
  - run `echo $LD_LIBRARY_PATH` confirm path
  - `import torch print(torch.backends.cudnn.version())` to comfirm cudnn version cnn901

- "Unable to load any of {libcudnn_ops.so.9.1.0, libcudnn_ops.so.9.1, libcudnn_ops.so.9, libcudnn_ops.so} Invalid handle. Cannot load symbol cudnnCreateTensorDescriptor."
  - pip install ctranslate2==4.4.0

- meet problems with ffmpeg
  - run `apt update && sudo apt install ffmpeg' or `conda install ffmpeg`

- libavcodec
 - run `ldconfig -p | grep libavcodec` you will see something like this:`libavcodec.so.58 (libc6,x86-64) => /lib/x86_64-linux-gnu/libavcodec.so.58`
 - export LD_LIBRARY_PATH=/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH && echo $LD_LIBRARY_PATH


### GPU Support with CUDA

#### Updating PyTorch for CUDA Support

To upgrade your PyTorch installation to enable GPU support with CUDA, follow these instructions based on your specific CUDA version. This is useful if you wish to enhance the performance of RealtimeSTT with CUDA capabilities.

#### For CUDA 11.8:
To update PyTorch and Torchaudio to support CUDA 11.8, use the following commands:

```bash
pip install torch==2.5.1+cu118 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118
```

#### For CUDA 12.X:
To update PyTorch and Torchaudio to support CUDA 12.X, execute the following:

```bash
pip install torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

Replace `2.5.1` with the version of PyTorch that matches your system and requirements.

#### Steps That Might Be Necessary Before

> **Note**: *To check if your NVIDIA GPU supports CUDA, visit the [official CUDA GPUs list](https://developer.nvidia.com/cuda-gpus).*

If you didn't use CUDA models before, some additional steps might be needed one time before installation. These steps prepare the system for CUDA support and installation of the **GPU-optimized** installation. This is recommended for those who require **better performance** and have a compatible NVIDIA GPU. To use RealtimeSTT with GPU support via CUDA please also follow these steps:

1. **Install NVIDIA CUDA Toolkit**:
    - select between CUDA 11.8 or CUDA 12.X Toolkit
        - for 12.X visit [NVIDIA CUDA Toolkit Archive](https://developer.nvidia.com/cuda-toolkit-archive) and select latest version.
        - for 11.8 visit [NVIDIA CUDA Toolkit 11.8](https://developer.nvidia.com/cuda-11-8-0-download-archive).
    - Select operating system and version.
    - Download and install the software.

2. **Install NVIDIA cuDNN**:
    - select between CUDA 11.8 or CUDA 12.X Toolkit
        - for 12.X visit [cuDNN Downloads](https://developer.nvidia.com/cudnn-downloads).
            - Select operating system and version.
            - Download and install the software.
        - for 11.8 visit [NVIDIA cuDNN Archive](https://developer.nvidia.com/rdp/cudnn-archive).
            - Click on "Download cuDNN v8.7.0 (November 28th, 2022), for CUDA 11.x".
            - Download and install the software.




## AI英语导师

<img width="667" alt="image" src="https://github.com/user-attachments/assets/89b2103b-0381-453b-bf81-5b4445e2d68b">


### 介绍

作为国人，包括我在内的大部分人即使认识英语，但是发音也及其不准确。

往往都是哑巴英语，能看不会说

以往英语口语主要靠外教或者英语角，大部分人出于各种各样的原因，时间成本、金钱成本。

当然，最重要的是，一个i人，平时说话都很少，怎么可能找人练习口语呢？

因此，一个AI英语导师自然而然可以解决部分问题。

我把她叫做Nana，来自《100样东西》中的手机助手名字，非常好听。


### 功能

项目主要集成了一些著名仓库的功能，包括：

- 语音识别： RealtimeSTT ,使用faster whisper模型进行近乎实时的语音识别。
- 文本转语音： RealtimeTTS, 使用各种STT引擎，如GTTS，Coqui等模型进行文本转语音。
- 文本对话： 使用基于mem0的记忆对话技术，实现对话历史的准确记忆，避免上下文的存储与复杂实现
- 将所有功能整合并提供前端界面，方便操作，实现服务的管理


### 如何使用

- 首先，你需要安装好python环境。
- 然后，你需要下载项目代码，并安装相关依赖库。
- 安装pytorch和cuda相关环境，详见 [GPU 支持与 CUDA](#gpu-支持与-cuda)
- 最后运行ai_voice_chat_app/main.py文件，打开浏览器，输入http://localhost:5000/ 即可进入主页。
- 运行后需要填写ai_voice_chat_app/config.txt相关配置，基本全部免费申请即可。
- 然后，你就可以和Nana愉快的对话了~（初次运行需要下载2G左右的模型，需要耐心等待）
- 注意：项目也可直接部署到服务器上，实现多人对话。但是目前原STT库Coqui模型还未实现并行，所以一个用户大概用coqui需要4G的显存。
  - 一个24G显存服务器大概可以支持5-6个用户同时对话。
  - 服务部署后，会自动分配服务实例超过300s自动销毁，也可以长时间运行在自己的主机上。


### 项目结构

- ai_voice_chat_app/ 项目主目录
  - app.py 主程序
  - config.txt 配置文件
  - main.py 启动文件
  - static/ 静态文件目录
    - react 前端打包的目录
  - websocket/ ws服务目录
  - services/ 语音识别、文本转语音服务目录
    - coqui_voice/ 克隆声音的语音文件
    - models/ 语音识别模型文件
    - service_management 服务管理文件
    - services_instance.py 服务实例及逻辑定义文件
    - 其他服务文件
- fronted/ 前端项目目录 
- requirements.txt 依赖库文件


### 流程图
![流程图](https://github.com/user-attachments/assets/0f37cc68-66f5-42a6-899c-a389ecb6b744)


### 一些问题解答

- 使用 Linux
  - 你可能需要运行以下命令：
    ```
    sudo apt-get update
    sudo apt-get install python3-dev
    sudo apt-get install portaudio19-dev
    ```
  - Linux 上这些库可以用 pip 安装。运行 `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12==9.*` 进行安装
  - 注意在启动 Python 之前可能需要设置 LD_LIBRARY_PATH。运行以下命令：
    ```
    export LD_LIBRARY_PATH=`python3 -c 'import os; import nvidia.cublas.lib; import nvidia.cudnn.lib; print(os.path.dirname(nvidia.cublas.lib.__file__) + ":" + os.path.dirname(nvidia.cudnn.lib.__file__))'`
    ```
      - 运行 `echo $LD_LIBRARY_PATH` 确认路径
        
  - 运行 `import torch print(torch.backends.cudnn.version())` 确认 cudnn 版本是 cnn901

- 遇到 "Unable to load any of {libcudnn_ops.so.9.1.0, libcudnn_ops.so.9.1, libcudnn_ops.so.9, libcudnn_ops.so} Invalid handle. Cannot load symbol cudnnCreateTensorDescriptor." 错误
  - 运行 `pip install ctranslate2==4.4.0`

- 遇到 ffmpeg 相关问题
  - 运行 `apt update && sudo apt install ffmpeg` 或 `conda install ffmpeg`

- libavcodec 相关
  - 运行 `ldconfig -p | grep libavcodec` 你会看到类似这样的输出：`libavcodec.so.58 (libc6,x86-64) => /lib/x86_64-linux-gnu/libavcodec.so.58`
  - 运行 `export LD_LIBRARY_PATH=/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH && echo $LD_LIBRARY_PATH`


### GPU 支持与 CUDA

#### 更新支持 CUDA 的 PyTorch

要升级您的 PyTorch 安装以启用 CUDA GPU 支持，请根据您的具体 CUDA 版本按照以下说明操作。如果您希望通过 CUDA 功能提升 RealtimeSTT 的性能，这将很有用。

#### CUDA 11.8：
要更新 PyTorch 和 Torchaudio 以支持 CUDA 11.8，使用以下命令：

```bash
pip install torch==2.5.1+cu118 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu118
```

#### CUDA 12.X：
要更新 PyTorch 和 Torchaudio 以支持 CUDA 12.X，执行以下命令：

```bash
pip install torch==2.5.1+cu121 torchaudio==2.5.1 --index-url https://download.pytorch.org/whl/cu121
```

将 `2.5.1` 替换为与您的系统和需求相匹配的 PyTorch 版本。

#### 可能需要的前期步骤

> **注意**：*要检查您的 NVIDIA GPU 是否支持 CUDA，请访问[官方 CUDA GPU 列表](https://developer.nvidia.com/cuda-gpus)。*

如果您之前没有使用过 CUDA 模型，在安装之前可能需要一些额外的一次性步骤。这些步骤为 CUDA 支持和安装 **GPU 优化版本**做准备。对于那些需要**更好性能**并拥有兼容 NVIDIA GPU 的用户，建议执行这些步骤。要通过 CUDA 使用 RealtimeSTT 的 GPU 支持，请按照以下步骤操作：

1. **安装 NVIDIA CUDA Toolkit**：
    - 在 CUDA 11.8 或 CUDA 12.X Toolkit 之间选择
        - 对于 12.X 访问 [NVIDIA CUDA Toolkit 存档](https://developer.nvidia.com/cuda-toolkit-archive) 并选择最新版本
        - 对于 11.8 访问 [NVIDIA CUDA Toolkit 11.8](https://developer.nvidia.com/cuda-11-8-0-download-archive)
    - 选择操作系统和版本
    - 下载并安装软件

2. **安装 NVIDIA cuDNN**：
    - 在 CUDA 11.8 或 CUDA 12.X Toolkit 之间选择
        - 对于 12.X 访问 [cuDNN 下载](https://developer.nvidia.com/cudnn-downloads)
            - 选择操作系统和版本
            - 下载并安装软件
        - 对于 11.8 访问 [NVIDIA cuDNN 存档](https://developer.nvidia.com/rdp/cudnn-archive)
            - 点击 "Download cuDNN v8.7.0 (November 28th, 2022), for CUDA 11.x"
            - 下载并安装软件

