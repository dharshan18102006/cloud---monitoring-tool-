from flask import Blueprint, jsonify
import psutil
import time

proc_bp = Blueprint('processes', __name__)

# Critical system processes that must NOT be killed
PROTECTED_PIDS   = {0, 4}
PROTECTED_NAMES  = {
    'system idle process', 'system', 'csrss.exe',
    'smss.exe', 'wininit.exe', 'winlogon.exe',
    'services.exe', 'lsass.exe', 'svchost.exe'
}

@proc_bp.route('/processes', methods=['GET'])
def get_processes():
    from app import current_stats
    if current_stats:
        return jsonify(current_stats.get('processes', []))
    return jsonify([])

@proc_bp.route('/stats', methods=['GET'])
def get_stats():
    import app
    stats = app.current_stats
    if not stats or os.environ.get('VERCEL'):
        stats = app.monitor.get_stats()
        app.current_stats = stats
    warnings = app.monitor.get_warnings(stats)
    return jsonify({'stats': stats, 'warnings': warnings})

@proc_bp.route('/kill_process/<int:pid>', methods=['POST'])
def kill_process(pid):
    # ── Safety guard ──────────────────────────────────────────
    if pid in PROTECTED_PIDS:
        return jsonify({
            'status': 'error',
            'message': f'PID {pid} is a critical OS process and cannot be terminated.'
        }), 403

    try:
        proc = psutil.Process(pid)
        name = proc.name()

        if name.lower() in PROTECTED_NAMES:
            return jsonify({
                'status': 'error',
                'message': f'"{name}" is a critical system process and cannot be terminated.'
            }), 403

        # ── Terminate ─────────────────────────────────────────
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            proc.kill()             # force-kill if SIGTERM not enough

        time.sleep(0.3)             # brief pause so process list updates

        # ── Emit updated list via Socket.IO ───────────────────
        from app import socketio, monitor, current_stats as cs
        updated = monitor.get_stats()

        # Update the global current_stats too
        import app as _app
        _app.current_stats = updated

        socketio.emit('process_update', updated['processes'])

        return jsonify({
            'status': 'success',
            'message': f'Process "{name}" (PID {pid}) terminated successfully.'
        })

    except psutil.NoSuchProcess:
        return jsonify({'status': 'error', 'message': f'PID {pid} not found.'}), 404

    except psutil.AccessDenied:
        return jsonify({
            'status': 'error',
            'message': f'Access denied — cannot terminate PID {pid}. Try running as Administrator.'
        }), 403

    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
