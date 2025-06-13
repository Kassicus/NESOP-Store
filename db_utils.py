import sqlite3
import os
import logging

# Get the absolute path to the database file
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'nesop_store.db'))

# Add logging to help debug database connection issues
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_connection():
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database at {DB_PATH}: {str(e)}")
        raise

def get_user(username):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT username, password, balance, is_admin FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        return user
    finally:
        conn.close()

def add_user(username, password, balance, is_admin=0):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password, balance, is_admin) VALUES (?, ?, ?, ?)', 
              (username, password, balance, is_admin))
    conn.commit()
    conn.close()

def update_balance(username, new_balance):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET balance = ? WHERE username = ?', (new_balance, username))
    conn.commit()
    conn.close()

def get_all_users():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT username, password, balance, is_admin FROM users')
    users = c.fetchall()
    conn.close()
    return users

def update_user(username, password=None, balance=None, is_admin=None):
    conn = get_db_connection()
    c = conn.cursor()
    if password is not None and balance is not None and is_admin is not None:
        c.execute('UPDATE users SET password = ?, balance = ?, is_admin = ? WHERE username = ?', 
                  (password, balance, is_admin, username))
    elif password is not None and balance is not None:
        c.execute('UPDATE users SET password = ?, balance = ? WHERE username = ?', (password, balance, username))
    elif password is not None and is_admin is not None:
        c.execute('UPDATE users SET password = ?, is_admin = ? WHERE username = ?', (password, is_admin, username))
    elif balance is not None and is_admin is not None:
        c.execute('UPDATE users SET balance = ?, is_admin = ? WHERE username = ?', (balance, is_admin, username))
    elif password is not None:
        c.execute('UPDATE users SET password = ? WHERE username = ?', (password, username))
    elif balance is not None:
        c.execute('UPDATE users SET balance = ? WHERE username = ?', (balance, username))
    elif is_admin is not None:
        c.execute('UPDATE users SET is_admin = ? WHERE username = ?', (is_admin, username))
    conn.commit()
    conn.close()

def delete_user(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def is_admin(username):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT is_admin FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result[0] == 1 if result else False

# --- Item CRUD ---
def get_items():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT item, description, price, image, sold_out, unlisted FROM items')
    items = c.fetchall()
    conn.close()
    return items

def get_item(item_name):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('SELECT item, description, price, image, sold_out, unlisted FROM items WHERE item = ?', (item_name,))
    item = c.fetchone()
    conn.close()
    return item

def add_item(item, description, price, image=None, sold_out=0, unlisted=0):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('INSERT INTO items (item, description, price, image, sold_out, unlisted) VALUES (?, ?, ?, ?, ?, ?)', (item, description, price, image, sold_out, unlisted))
    conn.commit()
    conn.close()

def update_item(item, description=None, price=None, image=None, sold_out=None, unlisted=None):
    conn = get_db_connection()
    c = conn.cursor()
    fields = []
    values = []
    if description is not None:
        fields.append('description = ?')
        values.append(description)
    if price is not None:
        fields.append('price = ?')
        values.append(price)
    if image is not None:
        fields.append('image = ?')
        values.append(image)
    if sold_out is not None:
        fields.append('sold_out = ?')
        values.append(sold_out)
    if unlisted is not None:
        fields.append('unlisted = ?')
        values.append(unlisted)
    if fields:
        values.append(item)
        c.execute(f'UPDATE items SET {", ".join(fields)} WHERE item = ?', values)
    conn.commit()
    conn.close()

def delete_item(item):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('DELETE FROM items WHERE item = ?', (item,))
    conn.commit()
    conn.close()