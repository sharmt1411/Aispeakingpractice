from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy

from auth.auth_routes import auth_bp
from chat.chat_routes import chat_bp
from database.database import db

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.secret_key = 'your_secret_key'



# 注册蓝图
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(chat_bp, url_prefix='/chat')


def init_logger():
    import logging
    level = logging.WARNING
    no_log_file = False

    log_format = 'RealTimeSTT: %(name)s - %(levelname)s - %(message)s'
    # Adjust file_log_format to include milliseconds
    file_log_format = '%(asctime)s.%(msecs)03d - ' + log_format

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)  # Set the root logger's level to DEBUG

    # Remove any existing handlers
    logger.handlers = []

    # Create a console handler and set its level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(log_format))

    # Add the handlers to the logger
    if not no_log_file :
        # Create a file handler and set its level
        file_handler = logging.FileHandler('realtimesst.log')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(
            file_log_format,
            datefmt='%Y-%m-%d %H:%M:%S'
        ))

        logger.addHandler(file_handler)
    logger.addHandler(console_handler)

@app.route('/')
def home() :
    return render_template("index.html")

if __name__ == '__main__':
    init_logger()
    app.run(debug=True)
    db.init_app(app)
    db.create_all()
