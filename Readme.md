## AI-English-Tutor

![interface screenshot](https://imgur.com/a/i5DZ73J)

Here's the English translation while maintaining the original structure:

### Introduction

As Chinese people, most of us, including myself, even though we recognize English, our pronunciation is extremely inaccurate.

We often have "mute English" - we can read but can't speak.

Traditionally, English speaking practice relied on foreign teachers or English corners, but most people couldn't participate due to various reasons like time and money costs.

Most importantly, as introverted people who rarely speak in general, how could we possibly find someone to practice speaking with?

Therefore, an AI English tutor naturally solves part of these problems.

I named her Nana, taken from the mobile assistant in "100 Things" - it's a very pleasant name.

### Features

The project mainly integrates functionalities from several famous repositories, including:

- Speech Recognition: RealtimeSTT, using faster whisper model for near real-time speech recognition.
- Text-to-Speech: RealtimeTTS, using various TTS engines like GTTS, Coqui models for text-to-speech conversion.
- Text Dialogue: Using mem0-based memory dialogue technology to achieve accurate conversation history recall, avoiding complex implementation of context storage.

### How to Use

- First, you need to have Python environment installed.
- Then, download the project code and install related dependencies.
- Finally, run ai_voice_chat_app/main.py file, open browser and enter http://localhost:5000/ to access the homepage.
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






## AI英语导师

![界面截图](https://imgur.com/a/i5DZ73J)

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

### 如何使用

- 首先，你需要安装好python环境。
- 然后，你需要下载项目代码，并安装相关依赖库。
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