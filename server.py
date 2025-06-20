from flask import Flask, request, jsonify, send_from_directory
import db_utils
import logging
from datetime import datetime
import os
from pathlib import Path

app = Flask(__name__, static_folder='.')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Get absolute path for upload folder
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'images'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Log the upload folder path
logging.info(f"Upload folder path: {UPLOAD_FOLDER}")

# Only log if directory exists and is writable
if os.path.exists(UPLOAD_FOLDER):
    if os.access(UPLOAD_FOLDER, os.W_OK):
        logging.info(f"Upload directory exists and is writable: {UPLOAD_FOLDER}")
    else:
        logging.error(f"Upload directory exists but is not writable: {UPLOAD_FOLDER}")
else:
    logging.error(f"Upload directory does not exist: {UPLOAD_FOLDER}")

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
    db_utils.add_user(username, password, 0, 0)  # Default is_admin=0
    logging.info(f"New user registered: {username}")
    return jsonify({'success': True})

@app.route('/api/check-admin', methods=['POST'])
def check_admin():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username required.'}), 400
    is_admin = db_utils.is_admin(username)
    return jsonify({'is_admin': is_admin})

# --- User Management (Admin) ---
@app.route('/api/users', methods=['GET'])
def get_users():
    users = db_utils.get_all_users()
    return jsonify({'users': [
        {'username': u[0], 'password': u[1], 'balance': u[2], 'is_admin': u[3]} for u in users
    ]})

@app.route('/api/users', methods=['POST'])
def add_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    balance = data.get('balance', 0)
    is_admin = data.get('is_admin', 0)
    if not username or not password:
        return jsonify({'error': 'Username and password required.'}), 400
    if db_utils.get_user(username):
        return jsonify({'error': 'Username already exists.'}), 409
    db_utils.add_user(username, password, balance, is_admin)
    logging.info(f"Admin added user: {username} (admin: {is_admin})")
    return jsonify({'success': True})

@app.route('/api/users', methods=['PUT'])
def update_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    balance = data.get('balance')
    is_admin = data.get('is_admin')
    if not username:
        return jsonify({'error': 'Username required.'}), 400
    if not db_utils.get_user(username):
        return jsonify({'error': 'User not found.'}), 404
    db_utils.update_user(username, password, balance, is_admin)
    logging.info(f"Admin updated user: {username} (admin: {is_admin})")
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
        {
            'item': i[0],
            'description': i[1],
            'price': i[2],
            'image': i[3],
            'sold_out': bool(i[4]) if len(i) > 4 else False,
            'unlisted': bool(i[5]) if len(i) > 5 else False
        } for i in items
    ]})

@app.route('/api/items', methods=['POST'])
def add_item():
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        item = request.form.get('item')
        description = request.form.get('description')
        price = request.form.get('price')
        image_file = request.files.get('image')
        sold_out = int(request.form.get('sold_out', 0))
        unlisted = int(request.form.get('unlisted', 0))
    else:
        data = request.get_json()
        item = data.get('item')
        description = data.get('description')
        price = data.get('price')
        image_file = None
        sold_out = int(data.get('sold_out', 0))
        unlisted = int(data.get('unlisted', 0))
    if not item or description is None or price is None:
        return jsonify({'error': 'Item, description, and price required.'}), 400
    if db_utils.get_item(item):
        return jsonify({'error': 'Item already exists.'}), 409
    image_filename = None
    if image_file and image_file.filename:
        ext = os.path.splitext(image_file.filename)[1].lower()
        safe_name = f"{item.replace(' ', '_')}_{int(datetime.now().timestamp())}{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, safe_name)
        image_file.save(image_path)
        image_filename = f"assets/images/{safe_name}"
    db_utils.add_item(item, description, float(price), image_filename, sold_out, unlisted)
    logging.info(f"Admin added item: {item} (image: {image_filename}, sold_out: {sold_out}, unlisted: {unlisted})")
    return jsonify({'success': True})

@app.route('/api/items', methods=['PUT'])
def update_item():
    if request.content_type and request.content_type.startswith('multipart/form-data'):
        item = request.form.get('item')
        description = request.form.get('description')
        price = request.form.get('price')
        image_file = request.files.get('image')
        sold_out = request.form.get('sold_out')
        unlisted = request.form.get('unlisted')
    else:
        data = request.get_json()
        item = data.get('item')
        description = data.get('description')
        price = data.get('price')
        image_file = None
        sold_out = data.get('sold_out')
        unlisted = data.get('unlisted')
    if not item:
        return jsonify({'error': 'Item required.'}), 400
    if not db_utils.get_item(item):
        return jsonify({'error': 'Item not found.'}), 404
    image_filename = None
    if image_file and image_file.filename:
        ext = os.path.splitext(image_file.filename)[1].lower()
        safe_name = f"{item.replace(' ', '_')}_{int(datetime.now().timestamp())}{ext}"
        image_path = os.path.join(UPLOAD_FOLDER, safe_name)
        image_file.save(image_path)
        image_filename = f"assets/images/{safe_name}"
    db_utils.update_item(
        item,
        description,
        float(price) if price is not None else None,
        image_filename,
        int(sold_out) if sold_out is not None else None,
        int(unlisted) if unlisted is not None else None
    )
    logging.info(f"Admin updated item: {item} (image: {image_filename}, sold_out: {sold_out}, unlisted: {unlisted})")
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

# Serve images from assets/images
@app.route('/assets/images/<path:filename>')
def serve_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(port=8000, debug=True) 