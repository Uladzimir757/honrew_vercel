# Файл: main.py (ВРЕМЕННЫЙ ДИАГНОСТИЧЕСКИЙ КОД)
import os
import json
from flask import Flask

_app = None

def get_app():
    global _app
    if _app is None:
        _app = Flask(__name__)

        @_app.route('/', defaults={'path': ''})
        @_app.route('/<path:path>')
        def catch_all(path):
            # Собираем все переменные окружения в словарь
            env_vars = dict(os.environ)
            
            # Выводим их в лог Vercel, чтобы мы могли их увидеть
            print("--- VERCEL ENVIRONMENT VARIABLES ---")
            print(json.dumps(env_vars, indent=2))
            print("------------------------------------")
            
            # Возвращаем их в виде JSON на страницу
            return env_vars
            
    return _app