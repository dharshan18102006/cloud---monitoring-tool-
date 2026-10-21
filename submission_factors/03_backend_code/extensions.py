from flask import Flask
from flask_cors import CORS
from flask_socketio import SocketIO
import os

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'system-monitor-secret-2024'
    CORS(app, supports_credentials=True, origins="*")
    socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')
    return app
