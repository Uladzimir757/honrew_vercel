# app/routers/auth.py
from flask import Blueprint, render_template, request, redirect, url_for, session, g

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def handle_login():
    # Ваша логика входа
    return render_template('auth/login.html')

# ИЛИ если у вас есть отдельный endpoint для GET запросов:
@auth_bp.route('/login', methods=['GET'])
def login():
    return render_template('auth/login.html')

@auth_bp.route('/login', methods=['POST'])
def login_post():
    # Обработка POST запроса
    pass
