# Файл: api/index.py (ВРЕМЕННЫЙ ДИАГНОСТИЧЕСКИЙ КОД)
import sys
import os

# Пустой объект Flask/WSGI, чтобы Vercel был доволен
def app(environ, start_response):
    # Получаем текущую рабочую директорию
    cwd = os.getcwd()
    
    # Получаем список всех путей, где Python ищет модули
    sys_path = "\n".join(sys.path)
    
    # Получаем список файлов и папок в корне проекта
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    root_contents = "\n".join(os.listdir(project_root))

    # Формируем ответ, который покажет нам всю эту информацию
    output = f"""
    --- Vercel Python Environment Diagnostics ---

    Current Working Directory:
    {cwd}

    -------------------------------------------

    Python Search Paths (sys.path):
    {sys_path}

    -------------------------------------------

    Contents of Project Root ({project_root}):
    {root_contents}
    """
    
    start_response('200 OK', [('Content-Type', 'text/plain')])
    return [output.encode('utf-8')]