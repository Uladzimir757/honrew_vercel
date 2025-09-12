import uvicorn

if __name__ == "__main__":
    # Эта строка говорит uvicorn найти объект 'app' в файле 'main' внутри пакета 'app'
    # reload=True автоматически перезапускает сервер при изменениях в коде
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)