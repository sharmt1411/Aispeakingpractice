from flask import Blueprint, request, redirect, render_template, session
from auth.models import User
from database.database import db

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    # 处理注册逻辑
    pass


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # 处理登录逻辑
    print("尝试登陆")
    return "登录页面2"
    pass


@auth_bp.route('/logout')
def logout():
    session.clear()
    return redirect('/auth/login')
