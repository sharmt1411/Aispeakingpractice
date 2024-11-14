from flask import Blueprint, request, jsonify, session
from services.speech_to_text import convert_speech_to_text
from services.text_processing import process_text
from services.text_to_speech import convert_text_to_speech
from chat.models import Chat
from database.database import db


chat_bp = Blueprint('chat', __name__)


@chat_bp.route('/voice_message', methods=['POST'])
def handle_voice_message() :
    audio_data = request.files['audio']

    # 1. 语音转文字
    text = convert_speech_to_text(audio_data)

    # 2. 文字处理
    processed_text = process_text(text)

    # 3. 文字转语音
    audio_response = convert_text_to_speech(processed_text)

    # 4. 存储聊天记录
    chat = Chat(user_id=session['user_id'], user_message=text, ai_response=processed_text)
    db.session.add(chat)
    db.session.commit()

    return jsonify({"audio_response" : audio_response})
