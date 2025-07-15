#!/usr/bin/env python3
"""
Active Directory Integration Database Migration Script
This script adds AD support to the existing NESOP Store database.
"""

import sqlite3
import os
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

# Get the absolute path to the database file
DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'nesop_store.db'))

def get_db_connection():
    """Get database connection"""
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database at {DB_PATH}: {str(e)}")
        raise

def backup_database():
    """Create a backup of the current database"""
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{DB_PATH}.backup_{timestamp}"
        
        # Copy the database file
        with open(DB_PATH, 'rb') as src:
            with open(backup_path, 'wb') as dst:
                dst.write(src.read())
        
        logger.info(f"Database backup created: {backup_path}")
        return backup_path
    except Exception as e:
        logger.error(f"Failed to create database backup: {str(e)}")
        raise

def check_existing_columns():
    """Check which columns already exist in the users table"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        c.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in c.fetchall()]
        logger.info(f"Existing users table columns: {columns}")
        return columns
    finally:
        conn.close()

def add_ad_columns_to_users():
    """Add AD-related columns to the users table"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Get existing columns first
        existing_columns = check_existing_columns()
        
        # Add user_type column if it doesn't exist
        if 'user_type' not in existing_columns:
            c.execute("ALTER TABLE users ADD COLUMN user_type TEXT DEFAULT 'local'")
            logger.info("Added 'user_type' column to users table")
        
        # Add ad_username column if it doesn't exist
        if 'ad_username' not in existing_columns:
            c.execute("ALTER TABLE users ADD COLUMN ad_username TEXT")
            logger.info("Added 'ad_username' column to users table")
        
        # Add ad_domain column if it doesn't exist
        if 'ad_domain' not in existing_columns:
            c.execute("ALTER TABLE users ADD COLUMN ad_domain TEXT")
            logger.info("Added 'ad_domain' column to users table")
        
        # Add ad_display_name column if it doesn't exist
        if 'ad_display_name' not in existing_columns:
            c.execute("ALTER TABLE users ADD COLUMN ad_display_name TEXT")
            logger.info("Added 'ad_display_name' column to users table")
        
        # Add ad_email column if it doesn't exist
        if 'ad_email' not in existing_columns:
            c.execute("ALTER TABLE users ADD COLUMN ad_email TEXT")
            logger.info("Added 'ad_email' column to users table")
        
        # Add last_ad_sync column if it doesn't exist
        if 'last_ad_sync' not in existing_columns:
            c.execute("ALTER TABLE users ADD COLUMN last_ad_sync DATETIME")
            logger.info("Added 'last_ad_sync' column to users table")
        
        # Add is_active column if it doesn't exist
        if 'is_active' not in existing_columns:
            c.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
            logger.info("Added 'is_active' column to users table")
        
        # Add created_at column if it doesn't exist
        if 'created_at' not in existing_columns:
            c.execute("ALTER TABLE users ADD COLUMN created_at DATETIME")
            logger.info("Added 'created_at' column to users table")
        
        # Add updated_at column if it doesn't exist
        if 'updated_at' not in existing_columns:
            c.execute("ALTER TABLE users ADD COLUMN updated_at DATETIME")
            logger.info("Added 'updated_at' column to users table")
        
        conn.commit()
        logger.info("Successfully added AD-related columns to users table")
        
    except sqlite3.OperationalError as e:
        if 'duplicate column name' in str(e):
            logger.info(f"Column already exists: {str(e)}")
        else:
            logger.error(f"Error adding columns to users table: {str(e)}")
            raise
    finally:
        conn.close()

def create_ad_config_table():
    """Create the ad_config table for storing AD settings"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Create ad_config table
        c.execute('''
            CREATE TABLE IF NOT EXISTS ad_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                server_url TEXT NOT NULL,
                domain TEXT NOT NULL,
                bind_dn TEXT,
                bind_password TEXT,
                user_base_dn TEXT,
                user_filter TEXT DEFAULT '(objectClass=user)',
                search_attributes TEXT DEFAULT 'sAMAccountName,displayName,mail,memberOf',
                is_enabled INTEGER DEFAULT 1,
                use_ssl INTEGER DEFAULT 1,
                port INTEGER DEFAULT 636,
                timeout INTEGER DEFAULT 10,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        logger.info("Created ad_config table")
        
        # Insert default/placeholder configuration
        c.execute('''
            INSERT OR IGNORE INTO ad_config (
                id, server_url, domain, bind_dn, user_base_dn, is_enabled
            ) VALUES (
                1, 'ldap://your-dc.yourdomain.com', 'yourdomain.com', 
                'CN=service_account,OU=Service Accounts,DC=yourdomain,DC=com',
                'OU=Users,DC=yourdomain,DC=com', 0
            )
        ''')
        
        conn.commit()
        logger.info("Successfully created ad_config table with default configuration")
        
    except Exception as e:
        logger.error(f"Error creating ad_config table: {str(e)}")
        raise
    finally:
        conn.close()

def create_ad_audit_log_table():
    """Create audit log table for AD operations"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Create ad_audit_log table
        c.execute('''
            CREATE TABLE IF NOT EXISTS ad_audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                ip_address TEXT,
                user_agent TEXT,
                success INTEGER DEFAULT 1,
                error_message TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        logger.info("Created ad_audit_log table")
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error creating ad_audit_log table: {str(e)}")
        raise
    finally:
        conn.close()

def create_fallback_admin():
    """Create a protected fallback admin account"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Check if fallback admin already exists
        c.execute("SELECT username FROM users WHERE username = 'fallback_admin'")
        existing_admin = c.fetchone()
        
        if not existing_admin:
            # Create fallback admin account
            c.execute('''
                INSERT INTO users (
                    username, password, balance, is_admin, user_type, 
                    is_active, created_at, updated_at
                ) VALUES (
                    'fallback_admin', 'ChangeMe123!', 0, 1, 'local', 
                    1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                )
            ''')
            
            logger.info("Created fallback admin account with username 'fallback_admin'")
            logger.warning("WARNING: Change the fallback admin password immediately!")
            logger.warning("Default password: ChangeMe123!")
        else:
            logger.info("Fallback admin account already exists")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error creating fallback admin: {str(e)}")
        raise
    finally:
        conn.close()

def update_existing_users():
    """Update existing users to set default values for new columns"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Update all existing users to have local user_type and be active
        c.execute('''
            UPDATE users 
            SET user_type = 'local', 
                is_active = 1,
                created_at = CURRENT_TIMESTAMP,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_type IS NULL OR user_type = ''
        ''')
        
        updated_count = c.rowcount
        logger.info(f"Updated {updated_count} existing users with default values")
        
        conn.commit()
        
    except Exception as e:
        logger.error(f"Error updating existing users: {str(e)}")
        raise
    finally:
        conn.close()

def create_indexes():
    """Create indexes for better performance"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_users_user_type ON users(user_type)",
            "CREATE INDEX IF NOT EXISTS idx_users_ad_username ON users(ad_username)",
            "CREATE INDEX IF NOT EXISTS idx_users_is_active ON users(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_ad_audit_log_username ON ad_audit_log(username)",
            "CREATE INDEX IF NOT EXISTS idx_ad_audit_log_action ON ad_audit_log(action)",
            "CREATE INDEX IF NOT EXISTS idx_ad_audit_log_created_at ON ad_audit_log(created_at)"
        ]
        
        for index_sql in indexes:
            c.execute(index_sql)
            logger.info(f"Created index: {index_sql.split('idx_')[1].split(' ')[0]}")
        
        conn.commit()
        logger.info("Successfully created database indexes")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {str(e)}")
        raise
    finally:
        conn.close()

def verify_migration():
    """Verify the migration was successful"""
    conn = get_db_connection()
    try:
        c = conn.cursor()
        
        # Check users table structure
        c.execute("PRAGMA table_info(users)")
        users_columns = [column[1] for column in c.fetchall()]
        logger.info(f"Users table columns after migration: {users_columns}")
        
        # Check ad_config table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_config'")
        ad_config_exists = c.fetchone()
        
        # Check ad_audit_log table exists
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ad_audit_log'")
        ad_audit_log_exists = c.fetchone()
        
        # Check fallback admin exists
        c.execute("SELECT username FROM users WHERE username = 'fallback_admin'")
        fallback_admin_exists = c.fetchone()
        
        logger.info(f"AD config table exists: {bool(ad_config_exists)}")
        logger.info(f"AD audit log table exists: {bool(ad_audit_log_exists)}")
        logger.info(f"Fallback admin exists: {bool(fallback_admin_exists)}")
        
        # Count users by type
        c.execute("SELECT user_type, COUNT(*) FROM users GROUP BY user_type")
        user_counts = c.fetchall()
        logger.info(f"User counts by type: {user_counts}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error verifying migration: {str(e)}")
        return False
    finally:
        conn.close()

def main():
    """Main migration function"""
    logger.info("Starting AD integration database migration...")
    
    try:
        # Create backup
        backup_path = backup_database()
        logger.info(f"Database backup created at: {backup_path}")
        
        # Run migration steps
        logger.info("Step 1: Adding AD columns to users table...")
        add_ad_columns_to_users()
        
        logger.info("Step 2: Creating AD configuration table...")
        create_ad_config_table()
        
        logger.info("Step 3: Creating AD audit log table...")
        create_ad_audit_log_table()
        
        logger.info("Step 4: Creating fallback admin account...")
        create_fallback_admin()
        
        logger.info("Step 5: Updating existing users...")
        update_existing_users()
        
        logger.info("Step 6: Creating database indexes...")
        create_indexes()
        
        logger.info("Step 7: Verifying migration...")
        if verify_migration():
            logger.info("✅ Migration completed successfully!")
            logger.info("Next steps:")
            logger.info("1. Change the fallback admin password")
            logger.info("2. Configure AD settings in the admin panel")
            logger.info("3. Test the authentication system")
        else:
            logger.error("❌ Migration verification failed!")
            
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        logger.error("You can restore from the backup if needed.")
        raise

if __name__ == "__main__":
    main() 