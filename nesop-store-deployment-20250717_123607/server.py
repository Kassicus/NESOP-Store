from flask import Flask, request, jsonify, send_from_directory
import db_utils
import logging
from datetime import datetime
import os
from pathlib import Path
import ad_utils
import config
import email_utils

# Initialize Flask app
app = Flask(__name__, static_folder='.')

def setup_local_development():
    """Setup for local development - ensures database exists and configuration is valid"""
    try:
        # Ensure database exists and is properly initialized
        if not os.path.exists('nesop_store.db'):
            logging.info("Database not found, initializing for local development...")
            init_local_database()
        
        # Test database connection
        try:
            conn = db_utils.get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users")
            conn.close()
            logging.info("Database connection verified")
        except Exception as e:
            logging.error(f"Database connection failed: {e}")
            init_local_database()
        
        # Ensure upload directory exists
        upload_dir = os.path.join(os.path.dirname(__file__), 'assets', 'images')
        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            logging.info(f"Created upload directory: {upload_dir}")
        
        logging.info("Local development setup completed successfully")
        
    except Exception as e:
        logging.error(f"Local development setup failed: {e}")
        raise

def init_local_database():
    """Initialize local database with required tables and fallback admin user"""
    try:
        conn = db_utils.get_db_connection()
        cursor = conn.cursor()
        
        # Create users table
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            balance INTEGER DEFAULT 0,
            is_admin INTEGER DEFAULT 0,
            user_type TEXT DEFAULT 'local',
            ad_username TEXT,
            ad_domain TEXT,
            ad_display_name TEXT,
            ad_email TEXT,
            last_ad_sync TIMESTAMP,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Create items table
        cursor.execute('''CREATE TABLE IF NOT EXISTS items (
            item TEXT PRIMARY KEY,
            description TEXT,
            price REAL,
            image TEXT,
            sold_out INTEGER DEFAULT 0,
            unlisted INTEGER DEFAULT 0
        )''')
        
        # Create purchases table
        cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            item TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            total_price REAL NOT NULL,
            purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (username) REFERENCES users(username),
            FOREIGN KEY (item) REFERENCES items(item)
        )''')
        
        # Create reviews table
        cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
            review_id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            username TEXT,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            review_text TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Create fallback admin user if not exists
        cursor.execute('''INSERT OR IGNORE INTO users (username, password, balance, is_admin, user_type) 
                          VALUES ('fallback_admin', 'ChangeMe123!', 1000, 1, 'local')''')
        
        # Create a test user for local development
        cursor.execute('''INSERT OR IGNORE INTO users (username, password, balance, is_admin, user_type) 
                          VALUES ('test_user', 'test123', 100, 0, 'local')''')
        
        conn.commit()
        conn.close()
        logging.info("Local database initialized successfully")
        
    except Exception as e:
        logging.error(f"Failed to initialize local database: {e}")
        raise

# Setup for local development
setup_local_development()

# Set environment variables for local development if not already set
if not os.getenv('AD_ENABLED'):
    os.environ['AD_ENABLED'] = 'False'
if not os.getenv('EMAIL_ENABLED'):
    os.environ['EMAIL_ENABLED'] = 'False'
if not os.getenv('USE_MOCK_AD'):
    os.environ['USE_MOCK_AD'] = 'True'

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

def print_local_development_info():
    """Print helpful information for local development"""
    try:
        print("\n" + "="*50)
        print("NESOP Store - Local Development")
        print("="*50)
        print(f"Server running on: http://127.0.0.1:8001")
        print(f"Database: {os.path.abspath('nesop_store.db')}")
        print(f"Upload folder: {os.path.abspath('assets/images')}")
        print("\nDefault accounts:")
        print("- Admin: fallback_admin / ChangeMe123!")
        print("- Test User: test_user / test123")
        print("\nAD Integration: Disabled (local development)")
        print("Email Notifications: Disabled (local development)")
        print("="*50)
        print()
    except Exception as e:
        logging.error(f"Error printing development info: {e}")

# Print development info
print_local_development_info()

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

@app.route('/api/place-order', methods=['POST'])
def place_order():
    """
    Place order endpoint with email notifications
    Handles order processing, balance updates, and email notifications
    """
    data = request.get_json()
    
    # Extract order data
    username = data.get('username')
    items = data.get('items', [])
    total = data.get('total', 0)
    order_date = data.get('order_date')
    order_time = data.get('order_time')
    
    # Validate required fields
    if not username or not items or not isinstance(total, (int, float)):
        logging.warning(f"Invalid place-order request: {data}")
        return jsonify({'error': 'Invalid request - missing required fields'}), 400
    
    # Check if user exists
    user = db_utils.get_user(username)
    if not user:
        logging.warning(f"User not found for order: {username}")
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has sufficient balance
    current_balance = float(user[2])  # Balance is the 3rd field
    if current_balance < total:
        logging.warning(f"Insufficient balance for order: {username}, balance: {current_balance}, total: {total}")
        return jsonify({'error': 'Insufficient balance'}), 400
    
    # Calculate new balance
    new_balance = current_balance - total
    
    try:
        # Update user balance
        db_utils.update_balance(username, new_balance)
        logging.info(f"Order processed - Balance updated for user {username}: {current_balance} -> {new_balance}")
        
        # Prepare order data for email notification
        order_data = {
            'username': username,
            'items': [{'name': item.get('item', ''), 'price': float(item.get('price', 0))} for item in items],
            'total': total,
            'new_balance': new_balance,
            'order_date': order_date or datetime.now().strftime('%Y-%m-%d'),
            'order_time': order_time or datetime.now().strftime('%H:%M:%S')
        }
        
        # Send email notification
        email_success = False
        email_message = ""
        
        try:
            email_success, email_message = email_utils.send_order_notification(order_data)
            if email_success:
                logging.info(f"Order notification email sent successfully for user {username}")
            else:
                logging.warning(f"Failed to send order notification email for user {username}: {email_message}")
        except Exception as e:
            logging.error(f"Error sending order notification email for user {username}: {str(e)}")
            email_message = f"Email notification error: {str(e)}"
        
        # Log order details
        order_summary = f"Order placed by {username} - Total: €{total:.2f} - Items: {len(items)}"
        logging.info(order_summary)
        
        # Return success response
        response = {
            'success': True,
            'message': 'Order placed successfully',
            'order_data': {
                'username': username,
                'total': total,
                'new_balance': new_balance,
                'items_count': len(items)
            },
            'email_notification': {
                'success': email_success,
                'message': email_message
            }
        }
        
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Error processing order for user {username}: {str(e)}")
        return jsonify({'error': 'Order processing failed', 'details': str(e)}), 500

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return jsonify({'error': 'Username and password required.'}), 400
    
    # Normalize username to prevent duplicates
    normalized_username = ad_utils.ActiveDirectoryManager.normalize_username(username)
    
    # Check if user already exists (both original and normalized)
    if db_utils.get_user(username) or db_utils.get_user(normalized_username):
        return jsonify({'error': 'Username already exists.'}), 409
    
    # Use normalized username for database storage
    db_utils.add_user(normalized_username, password, 0, 0)  # Default is_admin=0
    logging.info(f"New user registered: {username} (normalized: {normalized_username})")
    return jsonify({'success': True})

@app.route('/api/check-admin', methods=['POST'])
def check_admin():
    data = request.get_json()
    username = data.get('username')
    if not username:
        return jsonify({'error': 'Username required.'}), 400
    is_admin = db_utils.is_admin(username)
    return jsonify({'is_admin': is_admin})

# Rate limiting for login attempts
failed_attempts = {}
import time

def check_rate_limit(username, max_attempts=3, window_seconds=300):
    """
    Check if user has exceeded rate limit
    Returns True if rate limit exceeded, False otherwise
    """
    now = time.time()
    
    if username not in failed_attempts:
        failed_attempts[username] = []
    
    # Clean old attempts
    failed_attempts[username] = [
        attempt_time for attempt_time in failed_attempts[username]
        if now - attempt_time < window_seconds
    ]
    
    # Check if limit exceeded
    if len(failed_attempts[username]) >= max_attempts:
        return True
    
    return False

def record_failed_attempt(username):
    """Record a failed login attempt"""
    if username not in failed_attempts:
        failed_attempts[username] = []
    
    failed_attempts[username].append(time.time())

@app.route('/api/login', methods=['POST'])
def login():
    """
    FIXED: Single authentication endpoint that prevents AD account lockouts.
    No longer uses dual authentication fallback to prevent double attempts.
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'error': 'Username and password required.'}), 400
    
    # CRITICAL FIX: Normalize username ONCE at the beginning
    normalized_username = ad_utils.ActiveDirectoryManager.normalize_username(username)
    
    # CRITICAL FIX: Check rate limit to prevent rapid attempts
    if check_rate_limit(normalized_username):
        logging.warning(f"Rate limit exceeded for user: {normalized_username} (original: {username})")
        return jsonify({'error': 'Too many failed attempts. Please try again later.'}), 429
    
    # Initialize AD manager
    try:
        ad_manager = ad_utils.ActiveDirectoryManager()
        logging.info(f"Login attempt for user: {username} (normalized: {normalized_username})")
        
        # Check if AD is enabled
        if ad_manager.app_config.ad_config.is_enabled:
            # CRITICAL FIX: Only try AD authentication - NO fallback to local auth
            try:
                ad_auth_result = ad_manager.authenticate_user(normalized_username, password)
                
                if ad_auth_result[0]:  # AD authentication successful
                    logging.info(f"AD authentication successful for user: {normalized_username}")
                    
                    # Handle user import/sync
                    ad_user = ad_auth_result[1]
                    if ad_user:
                        local_user = db_utils.get_user(normalized_username)
                        
                        if not local_user:
                            # Import new AD user
                            logging.info(f"Importing new AD user to local database: {username} (normalized: {normalized_username})")
                            db_utils.add_ad_user(
                                username=normalized_username,
                                ad_username=ad_user.get('sAMAccountName', username),
                                ad_domain=ad_user.get('domain', ''),
                                ad_display_name=ad_user.get('displayName', username),
                                ad_email=ad_user.get('mail', ''),
                                is_admin=False  # New users are not admin by default
                            )
                            
                            # Log the import
                            ad_manager.log_audit_event(
                                normalized_username, 
                                'user_import', 
                                f'AD user imported to local database (original: {username}, normalized: {normalized_username})',
                                {'is_admin': False, 'original_username': username}
                            )
                        else:
                            # Update existing user's AD sync timestamp
                            db_utils.update_ad_sync_timestamp(normalized_username)
                            
                            # Log the login
                            ad_manager.log_audit_event(
                                normalized_username, 
                                'login_success', 
                                f'AD user logged in successfully (original: {username}, normalized: {normalized_username})'
                            )
                        
                        # Get updated user info using normalized username
                        user_info = db_utils.get_user(normalized_username)
                        return jsonify({
                            'success': True,
                            'user': {
                                'username': user_info[0],
                                'is_admin': bool(user_info[3]),
                                'user_type': user_info[4],
                                'display_name': user_info[7] or username
                            },
                            'auth_method': 'ad'
                        })
                else:
                    # CRITICAL FIX: AD authentication failed - do NOT try local auth
                    logging.warning(f"AD authentication failed for user: {normalized_username} (original: {username})")
                    record_failed_attempt(normalized_username)
                    ad_manager.log_audit_event(
                        normalized_username, 
                        'login_failed', 
                        f'AD authentication failed (original: {username}, normalized: {normalized_username})'
                    )
                    return jsonify({'error': 'Invalid username or password.'}), 401
                    
            except Exception as e:
                logging.error(f"AD authentication error for {normalized_username}: {str(e)}")
                record_failed_attempt(normalized_username)
                ad_manager.log_audit_event(
                    normalized_username, 
                    'authentication_error', 
                    f'AD authentication error: {str(e)}'
                )
                return jsonify({'error': 'Authentication service unavailable.'}), 503
        else:
            # AD is disabled - only allow local authentication
            logging.info(f"AD disabled - attempting local authentication for user: {normalized_username}")
            
            # Try both original and normalized username for local auth
            local_user = db_utils.get_user(username)
            if not local_user:
                local_user = db_utils.get_user(normalized_username)
                if local_user:
                    logging.info(f"Found user with normalized username: {normalized_username}")
            
            if local_user and local_user[1] == password:
                logging.info(f"Local authentication successful for user: {normalized_username}")
                return jsonify({
                    'success': True,
                    'user': {
                        'username': local_user[0],
                        'is_admin': bool(local_user[3]),
                        'user_type': local_user[4] or 'local',
                        'display_name': local_user[7] or username
                    },
                    'auth_method': 'local'
                })
            else:
                logging.warning(f"Local authentication failed for user: {normalized_username}")
                record_failed_attempt(normalized_username)
                return jsonify({'error': 'Invalid username or password.'}), 401
        
    except Exception as e:
        logging.error(f"Login error for user {username}: {str(e)}")
        return jsonify({'error': 'Internal server error.'}), 500

# --- AD User Management (Admin) ---
@app.route('/api/ad-users/search', methods=['POST'])
def search_ad_users():
    """
    Search for AD users
    """
    data = request.get_json()
    username = data.get('username')
    search_term = data.get('search_term', '*')
    limit = data.get('limit', 50)
    
    # Check if user is admin
    if not username or not db_utils.is_admin(username):
        return jsonify({'error': 'Admin access required.'}), 403
    
    try:
        ad_manager = ad_utils.ActiveDirectoryManager()
        
        # Check if AD is enabled
        if not ad_manager.app_config.ad_config.is_enabled:
            return jsonify({'error': 'AD integration is disabled.'}), 400
        
        # Search for AD users
        ad_users = ad_manager.search_users(search_term, limit)
        
        # Get list of users already imported
        local_users = db_utils.get_all_users()
        imported_usernames = set(user[0] for user in local_users if user[4] == 'ad')  # user_type == 'ad'
        
        # Add import status to each AD user
        for user in ad_users:
            user['imported'] = user.get('sAMAccountName', '') in imported_usernames
            # Admin permissions are managed locally, not from AD groups
            user['is_admin'] = False
        
        logging.info(f"Found {len(ad_users)} AD users for search term: {search_term}")
        return jsonify({
            'success': True,
            'users': ad_users,
            'total': len(ad_users),
            'search_term': search_term
        })
        
    except Exception as e:
        logging.error(f"Error searching AD users: {str(e)}")
        return jsonify({'error': 'Failed to search AD users.'}), 500

@app.route('/api/ad-users/import', methods=['POST'])
def import_ad_users():
    """
    Import selected AD users to local database
    """
    data = request.get_json()
    username = data.get('username')
    ad_usernames = data.get('ad_usernames', [])
    
    # Check if user is admin
    if not username or not db_utils.is_admin(username):
        return jsonify({'error': 'Admin access required.'}), 403
    
    if not ad_usernames:
        return jsonify({'error': 'No users selected for import.'}), 400
    
    try:
        ad_manager = ad_utils.ActiveDirectoryManager()
        
        # Check if AD is enabled
        if not ad_manager.app_config.ad_config.is_enabled:
            return jsonify({'error': 'AD integration is disabled.'}), 400
        
        imported_users = []
        failed_users = []
        
        for ad_username in ad_usernames:
            try:
                # Get AD user details
                ad_users = ad_manager.search_users(ad_username, 1)
                if not ad_users:
                    failed_users.append({'username': ad_username, 'error': 'User not found in AD'})
                    continue
                
                ad_user = ad_users[0]
                
                # Check if user already exists
                if db_utils.get_user(ad_username):
                    failed_users.append({'username': ad_username, 'error': 'User already exists'})
                    continue
                
                # Import user
                # Admin permissions are managed locally, not from AD groups
                is_admin = False
                success = db_utils.add_ad_user(
                    username=ad_username,
                    ad_username=ad_user.get('sAMAccountName', ad_username),
                    ad_domain=ad_user.get('domain', ''),
                    ad_display_name=ad_user.get('displayName', ad_username),
                    ad_email=ad_user.get('mail', ''),
                    is_admin=is_admin
                )
                
                if success:
                    imported_users.append({
                        'username': ad_username,
                        'display_name': ad_user.get('displayName', ad_username),
                        'email': ad_user.get('mail', ''),
                        'is_admin': is_admin
                    })
                    
                    # Log the import
                    ad_manager.log_audit_event(
                        ad_username,
                        'user_import',
                        f'AD user imported by admin: {username}',
                        {'imported_by': username, 'is_admin': is_admin}
                    )
                else:
                    failed_users.append({'username': ad_username, 'error': 'Failed to create user'})
                    
            except Exception as e:
                failed_users.append({'username': ad_username, 'error': str(e)})
        
        logging.info(f"AD import completed: {len(imported_users)} successful, {len(failed_users)} failed")
        
        return jsonify({
            'success': True,
            'imported': imported_users,
            'failed': failed_users,
            'total_imported': len(imported_users),
            'total_failed': len(failed_users)
        })
        
    except Exception as e:
        logging.error(f"Error importing AD users: {str(e)}")
        return jsonify({'error': 'Failed to import AD users.'}), 500

@app.route('/api/ad-users/sync', methods=['POST'])
def sync_ad_user():
    """
    Sync AD user information with local database
    """
    data = request.get_json()
    username = data.get('username')
    ad_username = data.get('ad_username')
    
    # Check if user is admin
    if not username or not db_utils.is_admin(username):
        return jsonify({'error': 'Admin access required.'}), 403
    
    if not ad_username:
        return jsonify({'error': 'AD username required.'}), 400
    
    try:
        ad_manager = ad_utils.ActiveDirectoryManager()
        
        # Check if AD is enabled
        if not ad_manager.app_config.ad_config.is_enabled:
            return jsonify({'error': 'AD integration is disabled.'}), 400
        
        # Get AD user details
        ad_users = ad_manager.search_users(ad_username, 1)
        if not ad_users:
            return jsonify({'error': 'User not found in AD.'}), 404
        
        ad_user = ad_users[0]
        
        # Sync user info
        success = ad_manager.sync_ad_user_to_local(ad_username, ad_user)
        
        if success:
            # Log the sync
            ad_manager.log_audit_event(
                ad_username,
                'user_sync',
                f'AD user synced by admin: {username}',
                {'synced_by': username}
            )
            
            return jsonify({
                'success': True,
                'message': f'User {ad_username} synced successfully'
            })
        else:
            return jsonify({'error': 'Failed to sync user.'}), 500
            
    except Exception as e:
        logging.error(f"Error syncing AD user {ad_username}: {str(e)}")
        return jsonify({'error': 'Failed to sync AD user.'}), 500

# --- User Management (Admin) ---
@app.route('/api/users', methods=['GET'])
def get_users():
    users = db_utils.get_all_users()
    return jsonify({'users': [
        {
            'username': u[0], 
            'password': u[1], 
            'balance': u[2], 
            'is_admin': u[3],
            'user_type': u[4],
            'ad_username': u[5],
            'ad_domain': u[6],
            'ad_display_name': u[7],
            'ad_email': u[8],
            'last_ad_sync': u[9],
            'is_active': u[10],
            'created_at': u[11],
            'updated_at': u[12]
        } for u in users
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
    
    # Normalize username to prevent duplicates
    normalized_username = ad_utils.ActiveDirectoryManager.normalize_username(username)
    
    # Check if user already exists (both original and normalized)
    if db_utils.get_user(username) or db_utils.get_user(normalized_username):
        return jsonify({'error': 'Username already exists.'}), 409
    
    # Use normalized username for database storage
    db_utils.add_user(normalized_username, password, balance, is_admin)
    logging.info(f"Admin added user: {username} (normalized: {normalized_username}, admin: {is_admin})")
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
    
    # Protect fallback admin account
    if db_utils.is_fallback_admin(username):
        return jsonify({'error': 'Cannot delete fallback admin account.'}), 403
    
    if not db_utils.get_user(username):
        return jsonify({'error': 'User not found.'}), 404
    
    # Use soft delete for AD users, hard delete for local users
    user = db_utils.get_user(username)
    if user and user[4] == 'ad':  # user_type is at index 4
        db_utils.deactivate_user(username)
        logging.info(f"Admin deactivated AD user: {username}")
    else:
        db_utils.delete_user(username)
        logging.info(f"Admin deleted local user: {username}")
    
    return jsonify({'success': True})

@app.route('/api/users/add-currency', methods=['POST'])
def add_currency_to_all_users_route():
    data = request.get_json()
    username = data.get('username')
    amount = data.get('amount')
    if not username or amount is None:
        logging.warning(f"Invalid add-currency request: {data}")
        return jsonify({'error': 'Username and amount required.'}), 400
    if not db_utils.is_admin(username):
        logging.warning(f"Unauthorized add-currency attempt by {username}.")
        return jsonify({'error': 'Admin privileges required.'}), 403
    try:
        amount = float(amount)
    except Exception:
        return jsonify({'error': 'Amount must be a number.'}), 400
    if amount == 0:
        return jsonify({'error': 'Amount must not be zero.'}), 400
    updated = db_utils.add_currency_to_all_users(amount)
    logging.info(f"Admin {username} added {amount} to all user balances. {updated} users updated.")
    return jsonify({'success': True, 'updated': updated})

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

@app.route('/api/email/status', methods=['GET'])
def email_status():
    """Get email configuration status"""
    try:
        status = email_utils.email_manager.get_email_status()
        return jsonify({
            'success': True,
            'email_config': status
        })
    except Exception as e:
        logging.error(f"Error getting email status: {str(e)}")
        return jsonify({'error': 'Failed to get email status', 'details': str(e)}), 500

@app.route('/api/email/test-connection', methods=['POST'])
def test_email_connection():
    """Test email server connection"""
    try:
        success, message = email_utils.test_email_connection()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logging.error(f"Error testing email connection: {str(e)}")
        return jsonify({'error': 'Failed to test email connection', 'details': str(e)}), 500

@app.route('/api/email/send-test', methods=['POST'])
def send_test_email():
    """Send test email"""
    try:
        success, message = email_utils.send_test_email()
        return jsonify({
            'success': success,
            'message': message
        })
    except Exception as e:
        logging.error(f"Error sending test email: {str(e)}")
        return jsonify({'error': 'Failed to send test email', 'details': str(e)}), 500

@app.route('/api/product/<item>', methods=['GET'])
def get_product(item):
    product = db_utils.get_item(item)
    if not product:
        logging.warning(f"Product not found: {item}")
        return jsonify({'error': 'Product not found'}), 404
    return jsonify({
        'item': product[0],
        'description': product[1],
        'price': product[2],
        'image': product[3],
        'sold_out': bool(product[4]) if len(product) > 4 else False,
        'unlisted': bool(product[5]) if len(product) > 5 else False
    })

@app.route('/api/product/<item>/reviews', methods=['GET'])
def get_product_reviews(item):
    reviews = db_utils.get_reviews_for_item(item)
    return jsonify({'reviews': [
        {
            'review_id': r[0],
            'item': r[1],
            'username': r[2],
            'rating': r[3],
            'review_text': r[4],
            'timestamp': r[5]
        } for r in reviews
    ]})

@app.route('/api/product/<item>/reviews', methods=['POST'])
def add_product_review(item):
    data = request.get_json()
    username = data.get('username')  # Can be None for anonymous
    rating = data.get('rating')
    review_text = data.get('review_text')
    if not rating or not review_text:
        return jsonify({'error': 'Rating and review text required.'}), 400
    try:
        rating = int(rating)
        if rating < 1 or rating > 5:
            raise ValueError
    except Exception:
        return jsonify({'error': 'Rating must be an integer between 1 and 5.'}), 400
    success = db_utils.add_review(item, username, rating, review_text)
    if not success:
        return jsonify({'error': 'Failed to add review.'}), 500
    logging.info(f"Review submitted for {item} by {username or 'anonymous'}.")
    return jsonify({'success': True})

@app.route('/api/product/<item>/reviews/<int:review_id>', methods=['DELETE'])
def delete_product_review(item, review_id):
    data = request.get_json() or {}
    username = data.get('username')
    if not username or not db_utils.is_admin(username):
        logging.warning(f"Unauthorized review delete attempt by {username} for review {review_id}.")
        return jsonify({'error': 'Admin privileges required.'}), 403
    success = db_utils.delete_review(review_id)
    if not success:
        return jsonify({'error': 'Failed to delete review.'}), 500
    logging.info(f"Admin {username} deleted review {review_id} for item {item}.")
    return jsonify({'success': True})

@app.route('/api/ad-config', methods=['GET'])
def get_ad_config():
    """Get AD configuration information for frontend"""
    try:
        ad_manager = ad_utils.ActiveDirectoryManager()
        config_info = {
            'enabled': ad_manager.app_config.ad_config.is_enabled,
            'simple_bind_mode': ad_manager.simple_bind_mode,
            'use_mock': ad_manager.app_config.ad_config.use_mock
        }
        return jsonify(config_info)
    except Exception as e:
        logging.error(f"Error getting AD config: {str(e)}")
        return jsonify({'error': 'Failed to get AD configuration'}), 500

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
    app.run(port=8001, debug=True) 