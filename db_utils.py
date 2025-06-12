import sqlite3

DB_PATH = 'nesop_store.db'

def get_user(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT username, password, balance, is_admin FROM users WHERE username = ?', (username,))
    user = c.fetchone()
    conn.close()
    return user  # Returns tuple or None

def add_user(username, password, balance, is_admin=0):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO users (username, password, balance, is_admin) VALUES (?, ?, ?, ?)', 
              (username, password, balance, is_admin))
    conn.commit()
    conn.close()

def update_balance(username, new_balance):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET balance = ? WHERE username = ?', (new_balance, username))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT username, password, balance, is_admin FROM users')
    users = c.fetchall()
    conn.close()
    return users

def update_user(username, password=None, balance=None, is_admin=None):
    conn = sqlite3.connect(DB_PATH)
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
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM users WHERE username = ?', (username,))
    conn.commit()
    conn.close()

def is_admin(username):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT is_admin FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    conn.close()
    return result[0] == 1 if result else False

# --- Item CRUD ---
def get_items():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT item, description, price, image FROM items')
    items = c.fetchall()
    conn.close()
    return items

def get_item(item_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT item, description, price, image FROM items WHERE item = ?', (item_name,))
    item = c.fetchone()
    conn.close()
    return item

def add_item(item, description, price, image=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO items (item, description, price, image) VALUES (?, ?, ?, ?)', (item, description, price, image))
    conn.commit()
    conn.close()

def update_item(item, description=None, price=None, image=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if description is not None and price is not None and image is not None:
        c.execute('UPDATE items SET description = ?, price = ?, image = ? WHERE item = ?', (description, price, image, item))
    elif description is not None and price is not None:
        c.execute('UPDATE items SET description = ?, price = ? WHERE item = ?', (description, price, item))
    elif description is not None and image is not None:
        c.execute('UPDATE items SET description = ?, image = ? WHERE item = ?', (description, image, item))
    elif price is not None and image is not None:
        c.execute('UPDATE items SET price = ?, image = ? WHERE item = ?', (price, image, item))
    elif description is not None:
        c.execute('UPDATE items SET description = ? WHERE item = ?', (description, item))
    elif price is not None:
        c.execute('UPDATE items SET price = ? WHERE item = ?', (price, item))
    elif image is not None:
        c.execute('UPDATE items SET image = ? WHERE item = ?', (image, item))
    conn.commit()
    conn.close()

def delete_item(item):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM items WHERE item = ?', (item,))
    conn.commit()
    conn.close()