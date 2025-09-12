# Файл: api/index.py (ВРЕМЕННЫЙ ДИАГНОСТИЧЕСКИЙ КОД)
import os
import json

def app(environ, start_response):
    # Собираем все переменные окружения в словарь
    env_vars = dict(os.environ)
    
    # Выводим их в лог Vercel, чтобы мы могли их увидеть
    print("--- VERCEL ENVIRONMENT VARIABLES (DIAGNOSTICS) ---")
    print(json.dumps(env_vars, indent=2))
    print("--------------------------------------------------")
    
    # Возвращаем их в виде JSON на страницу
    output = json.dumps(env_vars, indent=2).encode('utf-8')
    start_response('200 OK', [('Content-Type', 'application/json')])
    return [output]