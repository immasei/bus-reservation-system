def mongodb(request: Request):
    from main import app
    return app.database