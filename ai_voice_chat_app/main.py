import multiprocessing

import os
import time
import queue    # 用于定义空值异常
import threading
import logging
from multiprocessing import Process, Queue

from flask import Flask, send_from_directory
from flask_socketio import SocketIO

from services import ServiceManagement
from websocket import register_socket_events


def background_thread():
    """把服务进程的结果返回给前端，格式（user_id, service——type，data），如果是message事件，则格式为（user_id，message，content）"""
    print('>>>>>Websocket Event Background thread started')
    while not socket_stop_event.is_set():
        try:
            result = output_queue.get(block=True, timeout=1)
            if result:
                # if result[1] != "TTS-result":
                #     print('Websocket Event Background thread processing output:', result)
                user_id, service, data = result

                if user_id in connected_clients:
                    if service == "CHAT-response":
                        # print('Websocket Event Background thread route input CHAT-response:', data)
                        input_queue.put((user_id, "TTS", data))
                    elif service == "STT-result":
                        print('Websocket Event Background thread route input STT-result:', data)
                        input_queue.put((user_id, "CHAT", data))

                    socketio.emit(service, data, to=connected_clients[user_id])
        except queue.Empty:
            time.sleep(0.01)
            pass


def stop_server():
    socket_stop_event.set()
    print('Ws Server stopped')
    socket_stop_event.set()


def service_manager_process(input_queue, output_queue):
    print('>>>>Starting service manager process')
    service_manager = ServiceManagement(input_queue, output_queue)
    service_manager.start()
    service_manager.thread.join()
    print('>>>>Service manager process stopped')



if __name__ == '__main__':

    input_queue = Queue()  # 进程间通信队列
    output_queue = Queue()  # 进程间通信队列
    process = None
    try :
        multiprocessing.log_to_stderr()  # 启用多进程日志记录到标准错误流
        # logger = multiprocessing.get_logger()
        # logger.setLevel(logging.INFO)
        print('>>>>Starting service manager process')
        process = Process(target=service_manager_process, args=(input_queue, output_queue))
        process.start()

        time.sleep(10)   # 等待服务进程启动,用于调试观测

        print('>>>>Starting Ws Server')
        socketio = SocketIO(cors_allowed_origins="*", async_mode='threading',
                            ping_timeout=15, ping_interval=10, logger=False, engineio_logger=False)

        socket_stop_event = threading.Event()

        connected_clients = {}  # {user_id:sid}
        reverse_connected_clients = {}  # {sid:user_id}
        connected_clients_lock = threading.Lock()

        os.environ['ENV'] = 'development'

        app = Flask(__name__, static_folder='static/react')
        if os.environ.get('ENV') == 'development':
            print('Running in development mode')
            app.config['DEBUG'] = True
        else:
            print('Running in production mode')
            app.config['DEBUG'] = False

        # 处理首页路由
        # 主页路由
        @app.route("/", defaults={"path" : ""})
        @app.route("/<path:path>")
        def serve_react(path) :
            try :
                # 打印当前工作目录

                if path.startswith("static") :  # 处理静态资源
                    return send_from_directory(app.static_folder, path)
                elif path :  # 如果路径不为空，返回文件或 404
                    return send_from_directory(app.static_folder, path)
                # 根路径返回 index.html
                return send_from_directory(app.static_folder, "index.html")

            except Exception as e :
                print(f"Error: {str(e)}")
                return str(e), 500


        @app.route('/api/test')
        def test() :
            return {'message' : 'Server is running'}


        register_socket_events(socketio, input_queue, connected_clients, reverse_connected_clients, connected_clients_lock)

        socketio.init_app(app)
        socketio.start_background_task(target=background_thread)
        print('Ws Server started')
        socketio.run(app, debug=True, allow_unsafe_werkzeug=True, use_reloader=False)

        print('MAIN-Server stopped')
        input_queue.put(("stop", 'stop', 'stop'))
        process.join()
        print('Process joined')
        process.terminate()
        print('Process terminated')
    except KeyboardInterrupt:
        print('MAIN-Server keyboard stopped')
        input_queue.put(("stop", 'stop', 'stop'))
        if process:
            process.join()
            print('Process joined')
            process.terminate()
            print('Process terminated')
    finally:
        stop_server()
        print('wait for 10s')
        time.sleep(10)  # 给一点时间让其他线程响应
        if process:
            process.terminate()
            process.join(timeout=5)
        print('Process terminated')


