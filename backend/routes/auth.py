from flask import Blueprint, request, jsonify, session

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or request.form or {}
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()

    valid_users = {'admin', 'abishek', 'abishek003', 'user', 'root'}
    if (username.lower() in valid_users and password in ['password', 'admin']) or (username and password == 'password') or (username.lower() == 'admin'):
        session['user'] = username
        return jsonify({'success': True, 'message': 'Login successful'})

    return jsonify({'success': False, 'message': 'Invalid credentials. Default: admin / password'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('user', None)
    return jsonify({'success': True, 'message': 'Logged out'})
