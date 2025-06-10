from flask import Flask, request, jsonify, send_from_directory
import csv
import os

app = Flask(__name__, static_folder='.')

DATA_DIR = os.path.join('data')
USERS_CSV = os.path.join(DATA_DIR, 'users.csv')
ITEMS_CSV = os.path.join(DATA_DIR, 'items.csv')

@app.route('/api/update-balance', methods=['POST'])
def update_balance():
    data = request.get_json()
    username = data.get('username')
    new_balance = data.get('newBalance')
    if not username or not isinstance(new_balance, (int, float)):
        return jsonify({'error': 'Invalid request'}), 400

    # Read users.csv
    users = []
    updated = False
    with open(USERS_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username:
                row['balance'] = str(new_balance)
                updated = True
            users.append(row)

    if not updated:
        return jsonify({'error': 'User not found'}), 404

    # Write back to users.csv
    with open(USERS_CSV, 'w', newline='') as csvfile:
        fieldnames = ['username', 'password', 'balance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(users)

    return jsonify({'success': True})

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'error': 'Username and password required.'}), 400
    # Check for duplicate username
    with open(USERS_CSV, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['username'] == username:
                return jsonify({'error': 'Username already exists.'}), 409
    # Ensure file ends with newline before appending
    with open(USERS_CSV, 'rb+') as f:
        f.seek(0, 2)
        if f.tell() > 0:
            f.seek(-1, 2)
            last_char = f.read(1)
            if last_char != b'\n':
                f.write(b'\n')
    # Append new user
    with open(USERS_CSV, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([username, password, 0])
    return jsonify({'success': True})

# --- Admin CSV Management Endpoints ---

@app.route('/api/csv/<filename>', methods=['GET'])
def get_csv(filename):
    username = request.args.get('username')
    if username != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    if filename not in ['users.csv', 'items.csv']:
        return jsonify({'error': 'Invalid file'}), 400
    file_path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return jsonify({'content': content})

@app.route('/api/csv/<filename>', methods=['POST'])
def update_csv(filename):
    username = request.json.get('username')
    if username != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    if filename not in ['users.csv', 'items.csv']:
        return jsonify({'error': 'Invalid file'}), 400
    file_path = os.path.join(DATA_DIR, filename)
    new_content = request.json.get('content')
    if not isinstance(new_content, str):
        return jsonify({'error': 'Invalid content'}), 400
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return jsonify({'success': True})

# Serve static files (HTML, JS, CSS, etc.)
@app.route('/', defaults={'path': 'index.html'})
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

if __name__ == '__main__':
    app.run(port=8000, debug=True) 