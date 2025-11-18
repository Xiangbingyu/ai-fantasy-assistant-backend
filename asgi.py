# ai-fantasy-assistant-backend/asgi.py
from app import create_app
from app.routes.websocket import socketio

app = create_app()
asgi_app = socketio.asgi_app(app)  # 将 Flask 应用包装为 ASGI 应用