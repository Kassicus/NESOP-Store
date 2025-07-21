#!/usr/bin/env python3
"""
NESOP Store - Currency Transactions Migration
Adds currency_transactions table to track all currency additions with notes
"""

import sqlite3
import logging
from datetime import datetime
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection(db_path='nesop_store.db'):
    """Get database connection"""
    return sqlite3.connect(db_path)

def create_currency_transactions_table(db_path='nesop_store.db'):
    """Create the currency_transactions table"""
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Create currency_transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS currency_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                amount REAL NOT NULL,
                transaction_type TEXT NOT NULL DEFAULT 'admin_add',
                note TEXT,
                added_by TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (added_by) REFERENCES users(username)
            )
        ''')
        
        # Create index for better query performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_currency_transactions_username 
            ON currency_transactions(username)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_currency_transactions_created_at 
            ON currency_transactions(created_at DESC)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.info("Currency transactions table created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating currency transactions table: {str(e)}")
        return False

def migrate_existing_balance_changes(db_path='nesop_store.db'):
    """
    Optional: Create initial transaction records for existing users
    This creates a baseline 'initial_balance' transaction for each user
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Get all users with non-zero balances
        cursor.execute('SELECT username, balance FROM users WHERE balance > 0')
        users_with_balance = cursor.fetchall()
        
        if users_with_balance:
            # Create initial balance transactions for existing users
            for username, balance in users_with_balance:
                cursor.execute('''
                    INSERT INTO currency_transactions 
                    (username, amount, transaction_type, note, added_by, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    username,
                    balance,
                    'initial_balance',
                    'Existing balance at time of transaction system implementation',
                    'system',
                    datetime.now().isoformat()
                ))
            
            conn.commit()
            logger.info(f"Created initial balance transactions for {len(users_with_balance)} users")
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"Error creating initial balance transactions: {str(e)}")
        return False

def verify_migration(db_path='nesop_store.db'):
    """Verify the migration was successful"""
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='currency_transactions'
        ''')
        
        if cursor.fetchone():
            # Check table structure
            cursor.execute('PRAGMA table_info(currency_transactions)')
            columns = cursor.fetchall()
            
            expected_columns = [
                'id', 'username', 'amount', 'transaction_type', 
                'note', 'added_by', 'created_at'
            ]
            
            actual_columns = [col[1] for col in columns]
            
            for expected_col in expected_columns:
                if expected_col not in actual_columns:
                    logger.error(f"Missing column: {expected_col}")
                    return False
            
            # Check indexes
            cursor.execute('PRAGMA index_list(currency_transactions)')
            indexes = cursor.fetchall()
            
            logger.info("Currency transactions table verification passed")
            logger.info(f"Columns: {actual_columns}")
            logger.info(f"Indexes: {len(indexes)} created")
            
            conn.close()
            return True
        else:
            logger.error("Currency transactions table was not created")
            conn.close()
            return False
            
    except Exception as e:
        logger.error(f"Error verifying migration: {str(e)}")
        return False

def main():
    """Run the migration"""
    logger.info("Starting currency transactions migration...")
    
    # Check if database file exists
    db_path = 'nesop_store.db'
    if not os.path.exists(db_path):
        logger.error(f"Database file not found: {db_path}")
        return False
    
    # Create the table
    if not create_currency_transactions_table(db_path):
        logger.error("Failed to create currency transactions table")
        return False
    
    # Optionally migrate existing balances
    # Uncomment the next lines if you want to create initial transactions for existing balances
    # logger.info("Creating initial balance transactions...")
    # migrate_existing_balance_changes(db_path)
    
    # Verify migration
    if verify_migration(db_path):
        logger.info("Currency transactions migration completed successfully!")
        return True
    else:
        logger.error("Migration verification failed")
        return False

if __name__ == '__main__':
    success = main()
    exit(0 if success else 1) 