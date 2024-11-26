"""

"""
import multiprocessing
# import eventlet
# from eventlet import semaphore, tpool
# eventlet.monkey_patch()


import os
import time
import queue    # 用于定义空值异常
import threading
import logging
# from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Process, Queue

from flask import Flask, request
from flask_socketio import SocketIO

from services import ServiceManager

# eventlet.monkey_patch()

socketio = SocketIO(cors_allowed_origins="*", async_mode='threading', 
                    ping_timeout=15, ping_interval=10, logger=True, engineio_logger=False)

socket_stop_event = threading.Event()
# result_queue = Queue()

connected_clients = {}       # {user_id:sid}
reverse_connected_clients = {}        # {sid:user_id}
# connected_clients_processor = {}  # {user_id:audio_processor}
connected_clients_lock = threading.Lock()
# sem = semaphore.Semaphore()

# thread_pool = ThreadPoolExecutor(max_workers=4)


def background_thread():
    """把服务进程的结果返回给前端，格式（user_id, service——type，data），如果是message事件，则格式为（user_id，message，content）"""
    print('>>>>>Websocket Event Background thread started')
    while not socket_stop_event.is_set():
        try:
            result = output_queue.get(block=True, timeout=1)
            if result:
                user_id, service, data = result

                if user_id in connected_clients:
                    socketio.emit(service, data, to=connected_clients[user_id])
                    # print(f"Websocket Event Background thread processed event:,"
                    #              f"{service}, {data}, for user id:, {user_id}")
                # output_queue.task_done()
                # if event_name == 'realtime_result':  # 由客户端操作
                #     # /////////////////////////启动LLM服务/语音合成服务
                #     pass
        except queue.Empty:
            time.sleep(0.01)
            pass
            # result = result_queue.get(block=True, timeout=1)
            # if result:
            #     event_name = result.get('key')  # 包括 message，realtime_result, realtime, complete_result
            #     # print('Websocket Event Background thread processing event:', event_name)
            #     value= result.get('value')
            #     # print('Websocket Event Background thread processing result:', value)
            #     room = result.get('session_id')
            #     # print('Websocket Event Background thread processing room:', room)
            #     print("reverse_connected_clients:", reverse_connected_clients)
            #     if room in reverse_connected_clients:
            #         socketio.emit(event_name, value, to=room)
            #         print('Websocket Event Background thread processed event:',
            #         event_name, 'value:', value, 'for room:', room)
            #     result_queue.task_done()
            #     if event_name == 'realtime_result':
            #         # /////////////////////////启动LLM服务/语音合成服务
            #         pass

        # except queue.Empty():
        #     time.sleep(0.01)
        #     pass


def handle_register_event(user_id, sid):
    """处理用户id和sid的注册事件，开始后续处理服务实例的创建和启动等待"""
    print(f">>>>>Register event handled for user id:, {user_id}, {sid}, \n")
    with connected_clients_lock:
        old_sid = connected_clients.pop(user_id, None)
        if old_sid:
            reverse_connected_clients.pop(old_sid, None)
        # sem.release()
        print(f'New client connected with user id:, {user_id}')
    try:
        connected_clients[user_id] = sid
        reverse_connected_clients[sid] = user_id
        input_queue.put((user_id, "STT", ""))
        # audio_processor.run()   # 会阻塞，直到该线程结束
    except Exception as e:
        print('Error registering for user id:', user_id, e)
        socketio.emit('message', "failedregister", room=sid)

    # sem.acquire()
    # connected_clients_lock.acquire()
    # audio_processor = connected_clients_processor.get(user_id, None)
    # if not audio_processor:        # 没有用户id对应的处理器，创建并启动处理器
    #     # 清理可能存在的旧的sid表
    #     old_sid = connected_clients.pop(user_id, None)
    #     if old_sid:
    #         reverse_connected_clients.pop(old_sid, None)
    #     # sem.release()
    #     connected_clients_lock.release()
    #     print('New client connected with user id:', user_id)
    #     try:
    #         audio_processor = SpeechToTextService(result_queue, sid)
    #         print('Audio processor created for user id:', user_id)
    #
    #         # with sem:
    #         with connected_clients_lock:
    #             connected_clients[user_id] = sid
    #             reverse_connected_clients.pop(sid, None)
    #             reverse_connected_clients[sid] = user_id
    #             connected_clients_processor[user_id] = audio_processor
    #         # print('New client connected with user id:', user_id)
    #         socketio.emit('message', "readytotalk", room=sid)
    #
    #         # tpool.execute(audio_processor.run)
    #         thread = threading.Thread(target=audio_processor.run)
    #         thread.start()
    #
    #         # audio_processor.run()   # 会阻塞，直到该线程结束
    #     except Exception as e:
    #         print('Error starting audio processor for user id:', user_id, e)
    #         socketio.emit('message', "failedregister", room=sid)
    #
    # else:    # 客户端已经注册过，可能是断开重连，判断并更新sid
    #     print('Client already registered with user id:', user_id,'has a processor')
    #     old_sid = connected_clients.pop(user_id, None)
    #     if old_sid:
    #         reverse_connected_clients.pop(old_sid, None)
    #     connected_clients[user_id] = sid
    #     reverse_connected_clients[sid] = user_id
    #     connected_clients_processor[user_id].set_session_id(sid)
    #     print('Client already registered with user id:', user_id,'sid updated to:', sid)
    #     # sem.release()
    #     connected_clients_lock.release()
    #     socketio.emit('message', "readytotalk", room=sid)


def handle_disconnect_event(sid):
    # with sem:
    with connected_clients_lock:
        # 释放掉 connected_clients，和 reverse_connected_clients 里面的对应关系，后期可以判断是否又重连
        user_id = reverse_connected_clients.pop(sid, None)
        if user_id:
            connected_clients.pop(user_id, None)
    print('>>>>>>>>>Disconnect event received for sid:', sid, "删除用户id和sid的相互对应关系")
    # eventlet.sleep(15)   # 保持资源等待15s，防止释放后重连，浪费资源
    # time.sleep(15)   # 保持资源等待15s，防止释放后重连，浪费资源
    # # with sem:
    # with connected_clients_lock:
    #     if user_id in connected_clients:    # 客户端已经重连，不需要处理
    #         print('Client already reconnected with user:', user_id)
    #         return
    #     else:
    #         audio_processor = connected_clients_processor.pop(user_id, None)
    # if audio_processor is not None:
    #     print('>>>>>>>>Audio processor already wait 15s，stopping, user id:', user_id)
    #     audio_processor.stop()
    #     print('>>>>>>>>Audio processor stopped, user id:', user_id)


@socketio.on('connect')
def handle_connect():
    print(f">>>>>Client connected,session_id:, {request.sid}")
    socketio.emit('message', "connected", room=request.sid)
    try:
        socketio.emit('message', "connected", room=request.sid)
    except Exception as e:
        print(f'Error in handle_connect: {e}')


@socketio.on('disconnect')
def handle_disconnect():
    print('>>>>>>>Client disconnected')
    try:
        # tpool.execute(handle_disconnect_event, request.sid)
        # 也可使用socketio.start_background_task(target=handle_disconnect_event, sid=request.sid)
        thread = threading.Thread(target=handle_disconnect_event, args=(request.sid,))
        thread.start()
    except Exception as e:
        print(f'Error in handle_disconnect: {e}')


@socketio.on('register')
def handle_register(data):
    print('>>>>>>>Register event received')
    try:
        user_id = data.get('user_id')  # 从客户端获取的唯一标识符
        # tpool.execute(handle_register_event, user_id, request.sid)
        # 也可使用socketio.start_background_task(target=handle_register_event, user_id=user_id, sid=request.sid)
        # thread = threading.Thread(target=handle_register_event, args=(user_id, request.sid))
        # thread.start()
        handle_register_event(user_id, request.sid)
        socketio.emit('message', "start loading model...", room=request.sid)
    except Exception as e:
        print(f'Error in handle_register: {e}')


@socketio.on('audio_stream')
def handle_audio_stream(data):
    # print('>>>>>>>Received audio stream')
    data = data.get('data')
    # with sem:
    with connected_clients_lock:    
        user_id = reverse_connected_clients.get(request.sid, None)
        if user_id:
            # audio_processor = connected_clients_processor.get(user_id, None)
            input_queue.put((user_id, "STT", data))
    # if audio_processor:
    #     audio_processor.put_audio_data(data)


@socketio.on_error()
def error_handler(e):
    print('socketio.on_error---An error has occurred:', e)
    return False


def stop_server():
    socket_stop_event.set()
    print('Ws Server stopped')
    socket_stop_event.set()


def service_manager_process(input_queue, output_queue):
    logger = multiprocessing.get_logger()
    print('New process started')
    service_manager = ServiceManager(input_queue, output_queue)
    service_manager.start()
    service_manager.thread.join()


if __name__ == '__main__':
    try:
        multiprocessing.log_to_stderr()  # 启用多进程日志记录到标准错误流
        logger = multiprocessing.get_logger()
        logger.setLevel(logging.INFO)
        os.environ['ENV'] = 'development'
        app = Flask(__name__)
        if os.environ.get('ENV') == 'development':
            print('Running in development mode')
            app.config['DEBUG'] = True
        else:
            print('Running in production mode')
            app.config['DEBUG'] = False

        input_queue = Queue()     # 进程间通信队列
        output_queue = Queue()      # 进程间通信队列

        process = Process(target=service_manager_process, args=(input_queue, output_queue))
        process.start()

        socketio.init_app(app)
        socketio.start_background_task(target=background_thread)
        socketio.run(app, debug=True, allow_unsafe_werkzeug=True)

        print('MAIN-Server stopped')
        input_queue.put(("stop", 'stop', 'stop'))
        process.join()
        print('Process joined')
        process.terminate()
        print('Process terminated')
    except KeyboardInterrupt:
        # socket_stop_event.set()
        # print('KeyboardInterrupt received, stopping server',time.time())
        # for audio_processor_to_stop in connected_clients_processor.values():
        #     audio_processor_to_stop.stop()
        #
        # print('Server stopped',time.time())
        print('MAIN-Server keyboard stopped')
    finally:

        # socket_stop_event.set()    # 停止数据输入线程
        # input_queue.put(("stop", 'message', 'stop'))
        stop_server()
        print('wait for 10s')
        time.sleep(10)  # 给一点时间让其他线程响应
        process.terminate()
        process.join(timeout=5)
        print('Process terminated')
