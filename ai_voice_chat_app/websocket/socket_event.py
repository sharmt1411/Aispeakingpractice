import threading
import config

from flask import request


def register_socket_events(socketio, input_queue, connected_clients, reverse_connected_clients, connected_clients_lock):
    def handle_register_event(user_id, sid) :
        """处理用户id和sid的注册事件，开始后续处理服务实例的创建和启动等待"""
        print(f">>>>>Register event handled for user id:, {user_id}, {sid}, \n")
        with connected_clients_lock :
            old_sid = connected_clients.pop(user_id, None)
            if old_sid :
                reverse_connected_clients.pop(old_sid, None)
            # sem.release()
            print(f'New client connected with user id:, {user_id}')
        try :
            connected_clients[user_id] = sid
            reverse_connected_clients[sid] = user_id
            input_queue.put((user_id, "TTS", "start"))
            input_queue.put((user_id, "STT", "start"))
            input_queue.put((user_id, "CHAT", "start"))
            if config.TTS_ENGINE == "Coqui":
                socketio.emit('TTS-format', [8, 1, 24000], room=sid)
            else:
                socketio.emit('TTS-format', [8, 1, 22050], room=sid)
                print(f'WS-handle register emit TTS-format: {config.TTS_ENGINE}')
            # audio_processor.run()   # 会阻塞，直到该线程结束
        except Exception as e :
            print('Error registering for user id:', user_id, e)
            socketio.emit('message', "failedregister", room=sid)

    def handle_disconnect_event(sid) :
        # with sem:
        with connected_clients_lock :
            # 释放掉 connected_clients，和 reverse_connected_clients 里面的对应关系，后期可以判断是否又重连
            user_id = reverse_connected_clients.pop(sid, None)
            if user_id :
                connected_clients.pop(user_id, None)
        print('>>>>>>>>>Disconnect event received for sid:', sid, "删除用户id和sid的相互对应关系")

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
        if not data:
            return
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





