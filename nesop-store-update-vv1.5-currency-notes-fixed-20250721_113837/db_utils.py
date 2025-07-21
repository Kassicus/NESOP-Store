import sqlite3
import os
import logging

# Get the absolute path to the database file
# Default to development database, can be overridden by deployment config
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
        c.execute('''
            SELECT username, password, balance, is_admin, user_type, 
                   ad_username, ad_domain, ad_display_name, ad_email, 
                   last_ad_sync, is_active, created_at, updated_at 
            FROM users 
            WHERE username = ? AND is_active = 1
        ''', (username,))
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
    c.execute('''
        SELECT username, password, balance, is_admin, user_type, 
               ad_username, ad_domain, ad_display_name, ad_email, 
               last_ad_sync, is_active, created_at, updated_at 
        FROM users 
        ORDER BY created_at DESC
    ''')
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
    c.execute('SELECT is_admin FROM users WHERE username = ? AND is_active = 1', (username,))
    result = c.fetchone()
    conn.close()
    return result[0] == 1 if result else False

# --- AD User Management Functions ---

def add_ad_user(username, ad_username, ad_domain, ad_display_name=None, ad_email=None, balance=0, is_admin=0):
    """Add a new AD user to the local database"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO users (
                username, password, balance, is_admin, user_type, 
                ad_username, ad_domain, ad_display_name, ad_email, 
                is_active, created_at, updated_at
            ) VALUES (?, '', ?, ?, 'ad', ?, ?, ?, ?, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        ''', (username, balance, is_admin, ad_username, ad_domain, ad_display_name, ad_email))
        conn.commit()
        conn.close()
        logger.info(f"Added AD user: {username} ({ad_username}@{ad_domain})")
        return True
    except Exception as e:
        logger.error(f"Error adding AD user {username}: {str(e)}")
        return False

def get_ad_user_by_ad_username(ad_username, ad_domain):
    """Get user by AD username and domain"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('''
            SELECT username, password, balance, is_admin, user_type, 
                   ad_username, ad_domain, ad_display_name, ad_email, 
                   last_ad_sync, is_active, created_at, updated_at 
            FROM users 
            WHERE ad_username = ? AND ad_domain = ? AND is_active = 1
        ''', (ad_username, ad_domain))
        user = c.fetchone()
        return user
    finally:
        conn.close()

def update_ad_user_sync(username, ad_display_name=None, ad_email=None):
    """Update AD user information after sync"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE users 
        SET ad_display_name = ?, ad_email = ?, last_ad_sync = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
        WHERE username = ? AND user_type = 'ad'
    ''', (ad_display_name, ad_email, username))
    conn.commit()
    conn.close()

def get_users_by_type(user_type):
    """Get all users of a specific type (local or ad)"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT username, password, balance, is_admin, user_type, 
               ad_username, ad_domain, ad_display_name, ad_email, 
               last_ad_sync, is_active, created_at, updated_at 
        FROM users 
        WHERE user_type = ? 
        ORDER BY created_at DESC
    ''', (user_type,))
    users = c.fetchall()
    conn.close()
    return users

def deactivate_user(username):
    """Deactivate a user (soft delete)"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET is_active = 0, updated_at = CURRENT_TIMESTAMP WHERE username = ?', (username,))
    conn.commit()
    conn.close()
    logger.info(f"Deactivated user: {username}")

def reactivate_user(username):
    """Reactivate a user"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE username = ?', (username,))
    conn.commit()
    conn.close()
    logger.info(f"Reactivated user: {username}")

def is_fallback_admin(username):
    """Check if user is the protected fallback admin"""
    return username == 'fallback_admin'

# --- AD Configuration Functions ---

def get_ad_config():
    """Get current AD configuration"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT * FROM ad_config WHERE id = 1')
        config = c.fetchone()
        return config
    finally:
        conn.close()

def update_ad_config(server_url, domain, bind_dn, bind_password, user_base_dn, user_filter=None, is_enabled=1):
    """Update AD configuration"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE ad_config 
        SET server_url = ?, domain = ?, bind_dn = ?, bind_password = ?, 
            user_base_dn = ?, user_filter = ?, is_enabled = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    ''', (server_url, domain, bind_dn, bind_password, user_base_dn, user_filter or '(objectClass=user)', is_enabled))
    conn.commit()
    conn.close()
    logger.info(f"Updated AD configuration for domain: {domain}")

def is_ad_enabled():
    """Check if AD integration is enabled"""
    config = get_ad_config()
    return config and config[8] == 1  # is_enabled column

# --- AD Audit Log Functions ---

def log_ad_event(username, action, details=None, ip_address=None, user_agent=None, success=True, error_message=None):
    """Log AD authentication events"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO ad_audit_log (username, action, details, ip_address, user_agent, success, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (username, action, details, ip_address, user_agent, 1 if success else 0, error_message))
    conn.commit()
    conn.close()

def get_ad_audit_logs(limit=100):
    """Get recent AD audit logs"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''
        SELECT username, action, details, ip_address, success, error_message, created_at
        FROM ad_audit_log 
        ORDER BY created_at DESC 
        LIMIT ?
    ''', (limit,))
    logs = c.fetchall()
    conn.close()
    return logs

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

def get_reviews_for_item(item):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('SELECT review_id, item, username, rating, review_text, timestamp FROM reviews WHERE item = ? ORDER BY timestamp DESC', (item,))
        reviews = c.fetchall()
        return reviews
    except Exception as e:
        logger.error(f"Failed to fetch reviews for item {item}: {str(e)}")
        return []
    finally:
        conn.close()

def add_review(item, username, rating, review_text):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('INSERT INTO reviews (item, username, rating, review_text) VALUES (?, ?, ?, ?)', (item, username, rating, review_text))
        conn.commit()
        logger.info(f"Review added for item {item} by {username or 'anonymous'}.")
        return True
    except Exception as e:
        logger.error(f"Failed to add review for item {item}: {str(e)}")
        return False
    finally:
        conn.close()

def delete_review(review_id):
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute('DELETE FROM reviews WHERE review_id = ?', (review_id,))
        conn.commit()
        logger.info(f"Review {review_id} deleted.")
        return True
    except Exception as e:
        logger.error(f"Failed to delete review {review_id}: {str(e)}")
        return False
    finally:
        conn.close()

def add_currency_to_all_users(amount):
    """
    Increment the balance of all users by the specified amount.
    Returns the number of users updated.
    """
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET balance = balance + ?', (amount,))
    updated = c.rowcount
    conn.commit()
    conn.close()
    logger.info(f"Added {amount} to all user balances. {updated} users updated.")
    return updated

def update_ad_sync_timestamp(username: str) -> bool:
    """
    Update the last AD sync timestamp for a user
    
    Args:
        username (str): Username to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        
        c.execute('''
            UPDATE users 
            SET last_ad_sync = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE username = ?
        ''', (username,))
        
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            logger.info(f"Updated AD sync timestamp for user: {username}")
        else:
            logger.warning(f"User not found for AD sync update: {username}")
            
        return success
        
    except Exception as e:
        logger.error(f"Error updating AD sync timestamp for {username}: {str(e)}")
        return False

# --- Order Management Functions ---

def create_orders_table():
    """Create orders table if it doesn't exist"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                user_email TEXT,
                total_amount REAL NOT NULL,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'completed',
                email_sent INTEGER DEFAULT 0,
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        
        # Create order items table for order details
        c.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                item_name TEXT NOT NULL,
                item_price REAL NOT NULL,
                quantity INTEGER DEFAULT 1,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info("Orders tables created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating orders tables: {str(e)}")
        return False

def add_order(order_id: str, username: str, user_email: str, total_amount: float, items: list):
    """
    Add a new order to the database
    
    Args:
        order_id: Unique order identifier
        username: Username of the customer
        user_email: Email address of the customer
        total_amount: Total order amount
        items: List of order items with name and price
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Insert order
        c.execute('''
            INSERT INTO orders (order_id, username, user_email, total_amount, status)
            VALUES (?, ?, ?, ?, 'completed')
        ''', (order_id, username, user_email, total_amount))
        
        # Insert order items
        for item in items:
            c.execute('''
                INSERT INTO order_items (order_id, item_name, item_price, quantity)
                VALUES (?, ?, ?, ?)
            ''', (order_id, item.get('name', ''), item.get('price', 0), item.get('quantity', 1)))
        
        conn.commit()
        conn.close()
        logger.info(f"Order {order_id} added successfully for user {username}")
        return True
        
    except Exception as e:
        logger.error(f"Error adding order {order_id}: {str(e)}")
        return False

def get_order(order_id: str):
    """Get order details by order ID"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Get order info
        c.execute('''
            SELECT order_id, username, user_email, total_amount, order_date, status, email_sent
            FROM orders WHERE order_id = ?
        ''', (order_id,))
        order = c.fetchone()
        
        if not order:
            conn.close()
            return None
        
        # Get order items
        c.execute('''
            SELECT item_name, item_price, quantity
            FROM order_items WHERE order_id = ?
        ''', (order_id,))
        items = c.fetchall()
        
        conn.close()
        
        # Format result
        return {
            'order_id': order[0],
            'username': order[1],
            'user_email': order[2],
            'total_amount': order[3],
            'order_date': order[4],
            'status': order[5],
            'email_sent': order[6],
            'items': [{'name': item[0], 'price': item[1], 'quantity': item[2]} for item in items]
        }
        
    except Exception as e:
        logger.error(f"Error getting order {order_id}: {str(e)}")
        return None

def get_user_orders(username: str):
    """Get all orders for a specific user"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT order_id, user_email, total_amount, order_date, status, email_sent
            FROM orders WHERE username = ? ORDER BY order_date DESC
        ''', (username,))
        orders = c.fetchall()
        
        conn.close()
        
        return [
            {
                'order_id': order[0],
                'user_email': order[1],
                'total_amount': order[2],
                'order_date': order[3],
                'status': order[4],
                'email_sent': order[5]
            }
            for order in orders
        ]
        
    except Exception as e:
        logger.error(f"Error getting orders for user {username}: {str(e)}")
        return []

def mark_email_sent(order_id: str):
    """Mark an order's email as sent"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            UPDATE orders SET email_sent = 1 WHERE order_id = ?
        ''', (order_id,))
        
        success = c.rowcount > 0
        conn.commit()
        conn.close()
        
        if success:
            logger.info(f"Marked email as sent for order {order_id}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error marking email sent for order {order_id}: {str(e)}")
        return False

def get_all_orders():
    """Get all orders (admin function)"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT order_id, username, user_email, total_amount, order_date, status, email_sent
            FROM orders ORDER BY order_date DESC
        ''', )
        orders = c.fetchall()
        
        conn.close()
        
        return [
            {
                'order_id': order[0],
                'username': order[1],
                'user_email': order[2],
                'total_amount': order[3],
                'order_date': order[4],
                'status': order[5],
                'email_sent': order[6]
            }
            for order in orders
        ]
        
    except Exception as e:
        logger.error(f"Error getting all orders: {str(e)}")
        return []


# --- Currency Transaction Management Functions ---

def add_currency_with_transaction_log(username, amount, transaction_type, note, added_by):
    """
    Add currency to a specific user and log the transaction.
    
    Args:
        username (str): Username to add currency to
        amount (float): Amount to add (can be negative for deductions)
        transaction_type (str): Type of transaction ('admin_add', 'bulk_add', 'refund', etc.)
        note (str): Note explaining the transaction
        added_by (str): Username of the admin who performed the action
        
    Returns:
        dict: {'success': bool, 'new_balance': float, 'transaction_id': int}
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Start transaction
        c.execute('BEGIN TRANSACTION')
        
        # Get current balance
        c.execute('SELECT balance FROM users WHERE username = ?', (username,))
        user = c.fetchone()
        if not user:
            conn.rollback()
            conn.close()
            return {'success': False, 'error': 'User not found'}
        
        current_balance = user[0]
        new_balance = current_balance + amount
        
        # Update user balance
        c.execute('UPDATE users SET balance = ? WHERE username = ?', (new_balance, username))
        
        # Log the transaction
        c.execute('''
            INSERT INTO currency_transactions 
            (username, amount, transaction_type, note, added_by)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, amount, transaction_type, note, added_by))
        
        transaction_id = c.lastrowid
        
        # Commit transaction
        c.execute('COMMIT')
        conn.close()
        
        logger.info(f"Added {amount} to {username} balance. New balance: {new_balance}. Transaction ID: {transaction_id}")
        
        return {
            'success': True,
            'new_balance': new_balance,
            'transaction_id': transaction_id
        }
        
    except Exception as e:
        logger.error(f"Error adding currency to {username}: {str(e)}")
        try:
            c.execute('ROLLBACK')
            conn.close()
        except:
            pass
        return {'success': False, 'error': str(e)}

def add_currency_to_all_users_with_note(amount, note, added_by):
    """
    Add currency to all users and log individual transactions.
    
    Args:
        amount (float): Amount to add to each user
        note (str): Note explaining the bulk addition
        added_by (str): Username of the admin who performed the action
        
    Returns:
        dict: {'success': bool, 'updated': int, 'transaction_ids': list}
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Start transaction
        c.execute('BEGIN TRANSACTION')
        
        # Get all active users
        c.execute('SELECT username, balance FROM users WHERE is_active = 1')
        users = c.fetchall()
        
        transaction_ids = []
        updated_count = 0
        
        for username, current_balance in users:
            new_balance = current_balance + amount
            
            # Update user balance
            c.execute('UPDATE users SET balance = ? WHERE username = ?', (new_balance, username))
            
            # Log the transaction
            c.execute('''
                INSERT INTO currency_transactions 
                (username, amount, transaction_type, note, added_by)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, amount, 'bulk_add', note, added_by))
            
            transaction_ids.append(c.lastrowid)
            updated_count += 1
        
        # Commit transaction
        c.execute('COMMIT')
        conn.close()
        
        logger.info(f"Added {amount} to {updated_count} users. Created {len(transaction_ids)} transaction records.")
        
        return {
            'success': True,
            'updated': updated_count,
            'transaction_ids': transaction_ids
        }
        
    except Exception as e:
        logger.error(f"Error adding currency to all users: {str(e)}")
        try:
            c.execute('ROLLBACK')
            conn.close()
        except:
            pass
        return {'success': False, 'error': str(e)}

def get_user_currency_transactions(username, limit=50, offset=0):
    """
    Get currency transaction history for a specific user.
    
    Args:
        username (str): Username to get transactions for
        limit (int): Maximum number of transactions to return
        offset (int): Number of transactions to skip (for pagination)
        
    Returns:
        list: List of transaction dictionaries
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute('''
            SELECT id, username, amount, transaction_type, note, added_by, created_at
            FROM currency_transactions 
            WHERE username = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        ''', (username, limit, offset))
        
        transactions = c.fetchall()
        conn.close()
        
        return [
            {
                'id': tx[0],
                'username': tx[1],
                'amount': tx[2],
                'transaction_type': tx[3],
                'note': tx[4],
                'added_by': tx[5],
                'created_at': tx[6]
            }
            for tx in transactions
        ]
        
    except Exception as e:
        logger.error(f"Error getting transactions for user {username}: {str(e)}")
        return []

def get_all_currency_transactions(limit=100, offset=0, username_filter=None):
    """
    Get all currency transactions (admin function).
    
    Args:
        limit (int): Maximum number of transactions to return
        offset (int): Number of transactions to skip (for pagination)
        username_filter (str): Optional username to filter by
        
    Returns:
        list: List of transaction dictionaries
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        if username_filter:
            c.execute('''
                SELECT id, username, amount, transaction_type, note, added_by, created_at
                FROM currency_transactions 
                WHERE username = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (username_filter, limit, offset))
        else:
            c.execute('''
                SELECT id, username, amount, transaction_type, note, added_by, created_at
                FROM currency_transactions 
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            ''', (limit, offset))
        
        transactions = c.fetchall()
        conn.close()
        
        return [
            {
                'id': tx[0],
                'username': tx[1],
                'amount': tx[2],
                'transaction_type': tx[3],
                'note': tx[4],
                'added_by': tx[5],
                'created_at': tx[6]
            }
            for tx in transactions
        ]
        
    except Exception as e:
        logger.error(f"Error getting all currency transactions: {str(e)}")
        return []

def get_currency_transaction_count(username=None):
    """
    Get the total count of currency transactions.
    
    Args:
        username (str): Optional username to filter by
        
    Returns:
        int: Total number of transactions
    """
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        if username:
            c.execute('SELECT COUNT(*) FROM currency_transactions WHERE username = ?', (username,))
        else:
            c.execute('SELECT COUNT(*) FROM currency_transactions')
        
        count = c.fetchone()[0]
        conn.close()
        
        return count
        
    except Exception as e:
        logger.error(f"Error getting transaction count: {str(e)}")
        return 0

# Initialize orders table on import
create_orders_table()