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


@app.route('/')
def home() :
    return render_template("index.html")

if __name__ == '__main__':
    app.run(debug=True)
    db.init_app(app)
    db.create_all()
