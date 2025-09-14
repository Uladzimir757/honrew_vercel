# Файл: run.py (рекомендуемая версия)
from app.main import get_app

app = get_app()

if __name__ == "__main__":
    # Запускает встроенный сервер Flask, идеален для разработки
    app.run(debug=True, port=8000)