from flask import Flask, request, jsonify, send_from_directory
import db_utils
import logging
from datetime import datetime
import os
from pathlib import Path
import ad_utils
import config
import email_utils
import uuid
import stat
import grp
import pwd

app = Flask(__name__, static_folder='.')

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Get absolute path for upload folder
UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), 'assets', 'images'))
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def set_file_ownership_and_permissions(file_path):
    """Set correct ownership and permissions for uploaded files"""
    try:
        logging.info(f"Attempting to set ownership for: {file_path}")
        
        # Check if file exists
        if not os.path.exists(file_path):
            logging.error(f"File does not exist: {file_path}")
            return False
        
        # Get current file ownership for logging
        current_stat = os.stat(file_path)
        current_uid = current_stat.st_uid
        current_gid = current_stat.st_gid
        
        try:
            current_user = pwd.getpwuid(current_uid).pw_name
        except KeyError:
            current_user = str(current_uid)
        
        try:
            current_group = grp.getgrgid(current_gid).gr_name
        except KeyError:
            current_group = str(current_gid)
        
        logging.info(f"Current ownership: {current_user}:{current_group} ({current_uid}:{current_gid})")
        
        # Get nesop user ID
        try:
            nesop_uid = pwd.getpwnam('nesop').pw_uid
            logging.info(f"Target nesop UID: {nesop_uid}")
        except KeyError:
            # Fallback to current user if nesop doesn't exist
            nesop_uid = os.getuid()
            logging.warning("nesop user not found, using current user")
        
        # Get web server group ID (prefer www-data, fallback to nginx, then nesop)
        web_gid = None
        web_group = None
        for group_name in ['www-data', 'nginx', 'nesop']:
            try:
                web_gid = grp.getgrnam(group_name).gr_gid
                web_group = group_name
                logging.info(f"Found web server group: {web_group} (GID: {web_gid})")
                break
            except KeyError:
                continue
        
        if web_gid is None:
            logging.error("No suitable web server group found")
            return False
        
        # Check current process permissions
        current_process_uid = os.getuid()
        current_process_gid = os.getgid()
        logging.info(f"Current process running as: UID {current_process_uid}, GID {current_process_gid}")
        
        # Set ownership: nesop user, web server group
        logging.info(f"Setting ownership to: nesop:{web_group} ({nesop_uid}:{web_gid})")
        os.chown(file_path, nesop_uid, web_gid)
        
        # Set permissions: 664 (rw for owner and group, r for others)
        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
        
        # Verify the change worked
        new_stat = os.stat(file_path)
        new_uid = new_stat.st_uid
        new_gid = new_stat.st_gid
        
        try:
            new_user = pwd.getpwuid(new_uid).pw_name
        except KeyError:
            new_user = str(new_uid)
        
        try:
            new_group = grp.getgrgid(new_gid).gr_name
        except KeyError:
            new_group = str(new_gid)
        
        logging.info(f"✓ Successfully set ownership for {file_path}: {new_user}:{new_group} (664)")
        return True
        
    except PermissionError as e:
        logging.error(f"Permission denied when setting ownership for {file_path}: {e}")
        logging.error("The Flask process may not have permission to change file ownership")
        return False
    except Exception as e:
        logging.error(f"Failed to set ownership for {file_path}: {e}")
        return False

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
    Place a new order and send email confirmation
    """
    data = request.get_json()
    username = data.get('username')
    items = data.get('items', [])
    total = data.get('total', 0)
    
    if not username or not items or not isinstance(total, (int, float)) or total <= 0:
        logging.warning(f"Invalid place-order request: {data}")
        return jsonify({'error': 'Invalid request parameters'}), 400
    
    # Verify user exists
    user = db_utils.get_user(username)
    if not user:
        logging.warning(f"User not found for order: {username}")
        return jsonify({'error': 'User not found'}), 404
    
    # Check if user has sufficient balance
    user_balance = user[2]  # balance is the 3rd column
    if user_balance < total:
        logging.warning(f"Insufficient balance for user {username}: {user_balance} < {total}")
        return jsonify({'error': 'Insufficient balance'}), 400
    
    try:
        # Generate unique order ID
        order_id = f"NESOP-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8].upper()}"
        
        # Get fulfillment team email from configuration
        fulfillment_email = config.get_email_config().fulfillment_email
        
        # Format items for database storage
        formatted_items = []
        for item in items:
            formatted_items.append({
                'name': item.get('item', item.get('name', 'Unknown Item')),
                'price': item.get('price', 0),
                'quantity': 1  # Default quantity
            })
        
        # Add order to database (using fulfillment email for tracking)
        order_success = db_utils.add_order(order_id, username, fulfillment_email, total, formatted_items)
        if not order_success:
            return jsonify({'error': 'Failed to create order'}), 500
        
        # Update user balance and log transaction
        items_summary = ", ".join([f"{item['name']} (₦{item['price']})" for item in formatted_items])
        transaction_result = db_utils.add_currency_with_transaction_log(
            username=username,
            amount=-total,  # Negative for purchase
            transaction_type='purchase',
            note=f"Purchase: {items_summary} [Order: {order_id}]",
            added_by='system'
        )

        if not transaction_result['success']:
            return jsonify({'error': 'Failed to process payment'}), 500

        new_balance = transaction_result['new_balance']
        
        # Prepare order details for fulfillment team email
        order_details = {
            'order_id': order_id,
            'order_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'customer_username': username,
            'customer_display_name': user[7] if len(user) > 7 and user[7] else username,  # AD display name if available
            'items': formatted_items,
            'total': total,
            'customer_balance_after': new_balance
        }
        
        # Send email notification to fulfillment team
        fulfillment_email_sent = email_utils.send_order_notification(fulfillment_email, order_details)
        
        # Send order confirmation email to the user
        user_email_sent = email_utils.send_user_order_confirmation(username, order_details)
        
        # Mark email as sent if fulfillment email successful
        if fulfillment_email_sent:
            db_utils.mark_email_sent(order_id)
        
        # Log order completion
        logging.info(f"Order {order_id} placed successfully for user {username}, total: ₦{total}, fulfillment notification sent: {fulfillment_email_sent}, user notification sent: {user_email_sent}")
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'new_balance': new_balance,
            'email_sent': fulfillment_email_sent,
            'user_email_sent': user_email_sent,
            'message': f'Order placed successfully! Fulfillment team {"notified" if fulfillment_email_sent else "notification failed"}, user {"notified" if user_email_sent else "notification failed"}'
        })
        
    except Exception as e:
        logging.error(f"Error placing order for user {username}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

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

@app.route('/api/login', methods=['POST'])
def login():
    """
    Dual authentication endpoint that supports both AD and local users.
    Priority: AD authentication first, then local fallback.
    """
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    
    if not username or not password:
        return jsonify({'error': 'Username and password required.'}), 400
    
    # Initialize AD manager
    try:
        ad_manager = ad_utils.ActiveDirectoryManager()
        logging.info(f"Login attempt for user: {username}")
        
        # Step 1: Try AD authentication first (if AD is enabled)
        if ad_manager.app_config.ad_config.is_enabled:
            try:
                ad_auth_result = ad_manager.authenticate_user(username, password)
                if ad_auth_result[0]:  # Check if authentication was successful
                    logging.info(f"AD authentication successful for user: {username}")
                    
                    # Get AD user details from authentication result
                    ad_user = ad_auth_result[1]
                    if ad_user:
                        # Normalize username for database operations to prevent duplicates
                        normalized_username = ad_utils.ActiveDirectoryManager.normalize_username(
                            username, ad_manager.app_config.ad_config.domain
                        )
                        
                        # Check if user exists in local database using normalized username
                        local_user = db_utils.get_user(normalized_username)
                        
                        if not local_user:
                            # Import AD user to local database
                            logging.info(f"Importing new AD user to local database: {username} (normalized: {normalized_username})")
                            # New AD users are imported as regular users (not admin)
                            # Admin status can be granted later through the admin panel
                            is_admin = False
                            
                            # Create user in local database using normalized username
                            db_utils.add_ad_user(
                                username=normalized_username,
                                ad_username=ad_user.get('sAMAccountName', username),
                                ad_domain=ad_user.get('domain', ''),
                                ad_display_name=ad_user.get('displayName', username),
                                ad_email=ad_user.get('mail', ''),
                                is_admin=is_admin
                            )
                            
                            # Log the import
                            ad_manager.log_audit_event(
                                normalized_username, 
                                'user_import', 
                                f'AD user imported to local database (original: {username}, normalized: {normalized_username})',
                                {'is_admin': is_admin, 'original_username': username}
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
                        
            except Exception as e:
                logging.warning(f"AD authentication failed for {username}: {str(e)}")
                # Continue to local authentication fallback
        
        # Step 2: Local database authentication fallback
        logging.info(f"Attempting local authentication for user: {username}")
        
        # For local authentication, also try normalized username to handle existing users
        normalized_username = ad_utils.ActiveDirectoryManager.normalize_username(username)
        local_user = db_utils.get_user(username)
        
        # If no exact match, try normalized username
        if not local_user:
            local_user = db_utils.get_user(normalized_username)
            if local_user:
                logging.info(f"Found user with normalized username: {normalized_username}")
        
        if local_user and local_user[1] == password:  # Check password
            logging.info(f"Local authentication successful for user: {username}")
            
            # Log the login for local users
            if ad_manager.app_config.ad_config.is_enabled:
                ad_manager.log_audit_event(
                    local_user[0], 
                    'login_success', 
                    'Local user logged in successfully'
                )
            
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
        
        # Step 3: Authentication failed
        logging.warning(f"Authentication failed for user: {username}")
        if ad_manager.app_config.ad_config.is_enabled:
            ad_manager.log_audit_event(
                username, 
                'login_failed', 
                'Authentication failed for user'
            )
        
        return jsonify({'error': 'Invalid username or password.'}), 401
        
    except Exception as e:
        logging.error(f"Login error for user {username}: {str(e)}")
        return jsonify({'error': 'Authentication system error.'}), 500

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

@app.route('/api/users/add-currency-with-note', methods=['POST'])
def add_currency_with_note_route():
    """Add currency to a specific user with a note"""
    data = request.get_json()
    admin_username = data.get('admin_username')
    target_username = data.get('username')  # User to add currency to
    amount = data.get('amount')
    note = data.get('note', '')
    
    # Validation
    if not admin_username or not target_username or amount is None:
        logging.warning(f"Invalid add-currency-with-note request: {data}")
        return jsonify({'error': 'Admin username, target username, and amount required.'}), 400
    
    if not db_utils.is_admin(admin_username):
        logging.warning(f"Unauthorized add-currency-with-note attempt by {admin_username}.")
        return jsonify({'error': 'Admin privileges required.'}), 403
    
    try:
        amount = float(amount)
    except Exception:
        return jsonify({'error': 'Amount must be a number.'}), 400
    
    if amount == 0:
        return jsonify({'error': 'Amount must not be zero.'}), 400
    
    # Verify target user exists
    target_user = db_utils.get_user(target_username)
    if not target_user:
        return jsonify({'error': 'Target user not found.'}), 404
    
    # Add currency with transaction log
    result = db_utils.add_currency_with_transaction_log(
        username=target_username,
        amount=amount,
        transaction_type='admin_add',
        note=note,
        added_by=admin_username
    )
    
    if result['success']:
        logging.info(f"Admin {admin_username} added {amount} to {target_username}. New balance: {result['new_balance']}")
        return jsonify({
            'success': True,
            'new_balance': result['new_balance'],
            'transaction_id': result['transaction_id']
        })
    else:
        logging.error(f"Failed to add currency to {target_username}: {result.get('error')}")
        return jsonify({'error': result.get('error', 'Failed to add currency')}), 500

@app.route('/api/users/add-currency-bulk-with-note', methods=['POST'])
def add_currency_bulk_with_note_route():
    """Add currency to all users with a note"""
    data = request.get_json()
    admin_username = data.get('admin_username')
    amount = data.get('amount')
    note = data.get('note', '')
    
    # Validation
    if not admin_username or amount is None:
        logging.warning(f"Invalid add-currency-bulk-with-note request: {data}")
        return jsonify({'error': 'Admin username and amount required.'}), 400
    
    if not db_utils.is_admin(admin_username):
        logging.warning(f"Unauthorized add-currency-bulk-with-note attempt by {admin_username}.")
        return jsonify({'error': 'Admin privileges required.'}), 403
    
    try:
        amount = float(amount)
    except Exception:
        return jsonify({'error': 'Amount must be a number.'}), 400
    
    if amount == 0:
        return jsonify({'error': 'Amount must not be zero.'}), 400
    
    # Add currency to all users with transaction log
    result = db_utils.add_currency_to_all_users_with_note(
        amount=amount,
        note=note,
        added_by=admin_username
    )
    
    if result['success']:
        logging.info(f"Admin {admin_username} added {amount} to all users. Updated: {result['updated']}")
        return jsonify({
            'success': True,
            'updated': result['updated'],
            'transaction_count': len(result['transaction_ids'])
        })
    else:
        logging.error(f"Failed to add currency to all users: {result.get('error')}")
        return jsonify({'error': result.get('error', 'Failed to add currency')}), 500

@app.route('/api/users/<username>/transactions', methods=['GET'])
def get_user_transactions_route(username):
    """Get transaction history for a specific user"""
    # Check if user is requesting their own transactions or if they're an admin
    requesting_user = request.args.get('requesting_user')
    if not requesting_user:
        return jsonify({'error': 'Requesting user required.'}), 400
    
    # Users can only see their own transactions, admins can see any user's transactions
    if username != requesting_user and not db_utils.is_admin(requesting_user):
        logging.warning(f"Unauthorized transaction history access attempt by {requesting_user} for {username}")
        return jsonify({'error': 'Unauthorized access.'}), 403
    
    # Get pagination parameters
    try:
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        limit = min(limit, 100)  # Cap at 100
    except ValueError:
        return jsonify({'error': 'Invalid pagination parameters.'}), 400
    
    # Get transactions
    transactions = db_utils.get_user_currency_transactions(username, limit, offset)
    total_count = db_utils.get_currency_transaction_count(username)
    
    return jsonify({
        'success': True,
        'transactions': transactions,
        'total_count': total_count,
        'limit': limit,
        'offset': offset
    })

@app.route('/api/admin/transactions', methods=['GET'])
def get_all_transactions_route():
    """Get all currency transactions (admin only)"""
    requesting_user = request.args.get('requesting_user')
    if not requesting_user or not db_utils.is_admin(requesting_user):
        logging.warning(f"Unauthorized all-transactions access attempt by {requesting_user}")
        return jsonify({'error': 'Admin privileges required.'}), 403
    
    # Get pagination and filter parameters
    try:
        limit = int(request.args.get('limit', 100))
        offset = int(request.args.get('offset', 0))
        limit = min(limit, 200)  # Cap at 200 for admin
    except ValueError:
        return jsonify({'error': 'Invalid pagination parameters.'}), 400
    
    username_filter = request.args.get('username_filter')
    
    # Get transactions
    transactions = db_utils.get_all_currency_transactions(limit, offset, username_filter)
    total_count = db_utils.get_currency_transaction_count(username_filter)
    
    return jsonify({
        'success': True,
        'transactions': transactions,
        'total_count': total_count,
        'limit': limit,
        'offset': offset,
        'username_filter': username_filter
    })

@app.route('/api/admin/transactions/clear', methods=['POST'])
def clear_all_transactions_route():
    """Clear all currency transaction history (admin only)"""
    data = request.get_json()
    requesting_user = data.get('admin_username') if data else None
    
    if not requesting_user or not db_utils.is_admin(requesting_user):
        logging.warning(f"Unauthorized transaction clear attempt by {requesting_user}")
        return jsonify({'error': 'Admin privileges required.'}), 403
    
    # Get current transaction count before clearing
    total_count = db_utils.get_currency_transaction_count()
    
    if total_count == 0:
        return jsonify({
            'success': True, 
            'deleted_count': 0, 
            'message': 'No transactions to clear.'
        })
    
    # Clear all transactions
    result = db_utils.clear_all_currency_transactions(requesting_user)
    
    if result['success']:
        logging.info(f"Admin {requesting_user} cleared all currency transactions. {result['deleted_count']} records deleted.")
        return jsonify({
            'success': True,
            'deleted_count': result['deleted_count'],
            'message': f"Successfully cleared {result['deleted_count']} transaction records."
        })
    else:
        logging.error(f"Failed to clear transactions for admin {requesting_user}: {result.get('error')}")
        return jsonify({'error': result.get('error', 'Failed to clear transactions')}), 500

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
        # Set correct ownership and permissions for uploaded file
        set_file_ownership_and_permissions(image_path)
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
        # Set correct ownership and permissions for uploaded file
        set_file_ownership_and_permissions(image_path)
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
            'use_mock': ad_manager.app_config.use_mock_ad
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