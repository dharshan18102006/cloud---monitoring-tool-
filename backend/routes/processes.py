from flask import Blueprint, jsonify
import psutil

proc_bp = Blueprint('processes', __name__)

@proc_bp.route('/processes', methods=['GET'])
def get_processes():
    from app import current_stats
    if current_stats:
        return jsonify(current_stats.get('processes', []))
    return jsonify([])

@proc_bp.route('/kill_process/<int:pid>', methods=['POST'])
def kill_process(pid):
    try:
        p = psutil.Process(pid)
        p.terminate()
        p.wait(timeout=3)
        return jsonify({'success': True, 'message': f'Process {pid} terminated'})
    except psutil.NoSuchProcess:
        return jsonify({'success': False, 'message': 'Process not found'}), 404
    except psutil.AccessDenied:
        return jsonify({'success': False, 'message': 'Access denied'}), 403
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
