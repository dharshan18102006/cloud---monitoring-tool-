import sys
import os

# Add parent dir to path so "chatbot" package can be imported
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO
from prometheus_client import Gauge, CollectorRegistry, REGISTRY
import threading
import time
import pymongo

from system_monitor import SystemMonitor
from chatbot.engine import ChatbotEngine

# ---------------------------------------------------------------------------
# App Factory & Unified Frontend Serving
# ---------------------------------------------------------------------------
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend'))
app = Flask(__name__, static_folder=frontend_dir, static_url_path='')
app.config['SECRET_KEY'] = 'system-monitor-secret-2024'
CORS(app, supports_credentials=True, origins="*")
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

@app.route('/')
def serve_index():
    return send_from_directory(frontend_dir, 'login.html')

# ---------------------------------------------------------------------------
# Prometheus: use try/except to avoid duplicate-registration on reload
# ---------------------------------------------------------------------------
def _get_or_create_gauge(name, description):
    try:
        return Gauge(name, description)
    except ValueError:
        # Already registered (happens on Flask debug reloader)
        return REGISTRY._names_to_collectors.get(name)

cpu_gauge    = _get_or_create_gauge('system_cpu_usage',    'CPU usage percent')
memory_gauge = _get_or_create_gauge('system_memory_usage', 'Memory usage percent')
disk_gauge   = _get_or_create_gauge('system_disk_usage',   'Disk usage percent')
procs_gauge  = _get_or_create_gauge('system_active_procs', 'Number of running processes')

# ---------------------------------------------------------------------------
# MongoDB (optional – app works without it)
# ---------------------------------------------------------------------------
warnings_collection = None
mongo_uri = os.environ.get('MONGO_URI')
if mongo_uri:
    try:
        client = pymongo.MongoClient(mongo_uri, serverSelectionTimeoutMS=1500)
        client.server_info()
        warnings_collection = client['system_monitor_db']['warnings']
        print(f"[INFO] MongoDB connected to {mongo_uri}")
    except Exception as e:
        print(f"[WARN] MongoDB unavailable: {e} - running without DB")
elif not os.environ.get('VERCEL'):
    try:
        client = pymongo.MongoClient('mongodb://localhost:27017/', serverSelectionTimeoutMS=500)
        client.server_info()
        warnings_collection = client['system_monitor_db']['warnings']
        print("[INFO] MongoDB connected")
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Globals shared with routes (imported lazily there to avoid circular refs)
# ---------------------------------------------------------------------------
monitor        : SystemMonitor  = SystemMonitor()
chatbot_engine : ChatbotEngine  = ChatbotEngine()
current_stats  : dict           = None   # type: ignore

# ---------------------------------------------------------------------------
# Background broadcast thread
# ---------------------------------------------------------------------------
def _background():
    global current_stats
    while True:
        try:
            stats    = monitor.get_stats()
            warnings = monitor.get_warnings(stats)
            current_stats = stats

            if cpu_gauge:    cpu_gauge.set(stats['cpu']['total'])
            if memory_gauge: memory_gauge.set(stats['memory']['percent'])
            if disk_gauge:   disk_gauge.set(stats['disk']['percent'])
            if procs_gauge:  procs_gauge.set(len(stats['processes']))

            if warnings and warnings_collection is not None:
                try:
                    warnings_collection.insert_many([w.copy() for w in warnings])
                except Exception:
                    pass

            socketio.emit('system_data', {'stats': stats, 'warnings': warnings})
        except Exception as exc:
            print(f"Background thread error: {exc}")
        time.sleep(2)

threading.Thread(target=_background, daemon=True).start()

@socketio.on('connect')
def on_client_connect():
    global current_stats
    if current_stats:
        try:
            warnings = monitor.get_warnings(current_stats)
            socketio.emit('system_data', {'stats': current_stats, 'warnings': warnings})
        except Exception:
            pass

# ---------------------------------------------------------------------------
# Register Blueprints
# ---------------------------------------------------------------------------
from routes.auth      import auth_bp
from routes.processes import proc_bp
from routes.metrics   import metrics_bp
from routes.chat      import chat_bp

app.register_blueprint(auth_bp,    url_prefix='/api')
app.register_blueprint(proc_bp,    url_prefix='/api')
app.register_blueprint(metrics_bp, url_prefix='/api')
app.register_blueprint(chat_bp,    url_prefix='/api')

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    # use_reloader=False prevents the double-registration issue entirely
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
