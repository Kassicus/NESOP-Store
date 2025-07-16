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