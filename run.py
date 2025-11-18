from app import create_app
from app.routes.websocket import socketio
from app.logging_config import setup_logging, log_startup_info

# 配置日志系统
setup_logging()
log_startup_info()

app = create_app()

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=4000, debug=True)