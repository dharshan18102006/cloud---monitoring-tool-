from flask import Blueprint, request, jsonify

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat', methods=['POST'])
def chat():
    from app import current_stats, chatbot_engine, monitor
    data = request.get_json(force=True)
    message = data.get('message', '')

    stats = current_stats
    if stats:
        warnings = monitor.get_warnings(stats)
        top = stats['processes'][0]['name'] if stats['processes'] else 'None'
        formatted = {
            'cpu': stats['cpu']['total'],
            'memory': stats['memory']['percent'],
            'disk': stats['disk']['percent'],
            'top_process': top,
            'warning_count': len(warnings)
        }
    else:
        formatted = {'cpu': 0, 'memory': 0, 'disk': 0, 'top_process': 'None', 'warning_count': 0}

    response = chatbot_engine.generate_response(message, formatted)
    return jsonify({'response': response})
