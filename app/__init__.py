# 顶部导入区域
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from app.routes.llm import llm_bp
from app.routes.db import db_bp
from app.routes.websocket import websocket_bp, socketio
from app.models import db
from app.config import Config

def create_app() -> Flask:
    static_folder = os.path.join(os.path.dirname(__file__), "..", "frontend")
    app = Flask(__name__, static_folder=static_folder, static_url_path="")
    CORS(app)  # 允许跨域请求

    app.config.from_object(Config)
    db.init_app(app)
    
    # 初始化SocketIO
    socketio.init_app(app)
    
    # 注册路由蓝图
    app.register_blueprint(llm_bp)
    app.register_blueprint(db_bp)
    app.register_blueprint(websocket_bp)

    @app.route("/api/status")
    def status():
        return jsonify({"status": "ok", "message": "Backend API is running"})

    @app.route("/")
    def index():
        return app.send_static_file("index.html")
    
    # 创建数据库表（生产环境建议使用迁移工具）
    with app.app_context():
        db.create_all()

    return app