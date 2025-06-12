from flask import Flask, request, jsonify, send_from_directory
import db_utils
import logging
from datetime import datetime

app = Flask(__name__, static_folder='.')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

@app.route('/api/update-balance', methods=['POST'])
def update_balance():
    data = request.get_json()
    username = data.get('username')
    new_balance = data.get('newBalance')
    if not username or not isinstance(new_balance, (int, float)):
        logging.warning(f"Invalid update-balance request: {data}")
        return jsonify({'error': 'Invalid request'}), 400
    user = db_utils.get_user(username)
    if not user:
        logging.warning(f"User not found for balance update: {username}")
        return jsonify({'error': 'User not found'}), 404
    db_utils.update_balance(username, new_balance)
    logging.info(f"Balance updated for user {username} to {new_balance}")
    return jsonify({'success': True})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'error': 'Username and password required.'}), 400
    if db_utils.get_user(username):
        return jsonify({'error': 'Username already exists.'}), 409
    db_utils.add_user(username, password, 0)
    logging.info(f"New user registered: {username}")
    return jsonify({'success': True})

# --- User Management (Admin) ---
@app.route('/api/users', methods=['GET'])
def get_users():
    users = db_utils.get_all_users()
    return jsonify({'users': [
        {'username': u[0], 'password': u[1], 'balance': u[2]} for u in users
    ]})

@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    balance = data.get('balance', 0)
    if not username or not password:
        return jsonify({'error': 'Username and password required.'}), 400
    if db_utils.get_user(username):
        return jsonify({'error': 'Username already exists.'}), 409
    db_utils.add_user(username, password, balance)
    logging.info(f"Admin added user: {username}")
    return jsonify({'success': True})

@app.route('/api/users', methods=['PUT'])
def update_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    balance = data.get('balance')
    if not username:
        return jsonify({'error': 'Username required.'}), 400
    if not db_utils.get_user(username):
        return jsonify({'error': 'User not found.'}), 404
    db_utils.update_user(username, password, balance)
    logging.info(f"Admin updated user: {username}")
    return jsonify({'success': True})

@app.route('/api/users', methods=['DELETE'])
def delete_user():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username required.'}), 400
    if not db_utils.get_user(username):
        return jsonify({'error': 'User not found.'}), 404
    db_utils.delete_user(username)
    logging.info(f"Admin deleted user: {username}")
    return jsonify({'success': True})

# --- Item Management (Admin) ---
@app.route('/api/items', methods=['GET'])
def get_items():
    items = db_utils.get_items()
    return jsonify({'items': [
        {'item': i[0], 'description': i[1], 'price': i[2]} for i in items
    ]})

@app.route('/api/items', methods=['POST'])
def add_item():
    data = request.get_json()
    item = data.get('item')
    description = data.get('description')
    price = data.get('price')
    if not item or description is None or price is None:
        return jsonify({'error': 'Item, description, and price required.'}), 400
    if db_utils.get_item(item):
        return jsonify({'error': 'Item already exists.'}), 409
    db_utils.add_item(item, description, price)
    logging.info(f"Admin added item: {item}")
    return jsonify({'success': True})

@app.route('/api/items', methods=['PUT'])
def update_item():
    data = request.get_json()
    item = data.get('item')
    description = data.get('description')
    price = data.get('price')
    if not item:
        return jsonify({'error': 'Item required.'}), 400
    if not db_utils.get_item(item):
        return jsonify({'error': 'Item not found.'}), 404
    db_utils.update_item(item, description, price)
    logging.info(f"Admin updated item: {item}")
    return jsonify({'success': True})

@app.route('/api/items', methods=['DELETE'])
def delete_item():
    data = request.get_json()
    item = data.get('item')
    if not item:
        return jsonify({'error': 'Item required.'}), 400
    if not db_utils.get_item(item):
        return jsonify({'error': 'Item not found.'}), 404
    db_utils.delete_item(item)
    logging.info(f"Admin deleted item: {item}")
    return jsonify({'success': True})

# Serve static files (HTML, JS, CSS, etc.)
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(port=8000, debug=True) 