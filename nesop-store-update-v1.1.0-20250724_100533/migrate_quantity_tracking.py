#!/usr/bin/env python3
"""
Migration script to add quantity tracking to items table.
This adds a quantity column to track inventory levels.
"""

import sqlite3
import logging
import sys
import os

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_db_connection(db_path='nesop_store.db'):
    """Get database connection"""
    try:
        conn = sqlite3.connect(db_path)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def migrate_add_quantity_column(db_path='nesop_store.db'):
    """Add quantity column to items table"""
    conn = get_db_connection(db_path)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if items table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
        if not cursor.fetchone():
            logging.info(f"Items table does not exist in {db_path}, skipping migration")
            return True
        
        # Check if quantity column already exists
        cursor.execute("PRAGMA table_info(items)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'quantity' in columns:
            logging.info("Quantity column already exists in items table")
            return True
        
        # Add quantity column with default value of 0
        cursor.execute('ALTER TABLE items ADD COLUMN quantity INTEGER DEFAULT 0')
        logging.info("Added 'quantity' column to items table")
        
        # Update existing items to have a default quantity of 0
        # Admin can then update these manually
        cursor.execute('UPDATE items SET quantity = 0 WHERE quantity IS NULL')
        logging.info("Initialized quantity values for existing items")
        
        conn.commit()
        logging.info("Migration completed successfully")
        return True
        
    except sqlite3.Error as e:
        logging.error(f"Migration failed: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def validate_migration(db_path='nesop_store.db'):
    """Validate that the migration was successful"""
    conn = get_db_connection(db_path)
    if not conn:
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if quantity column exists
        cursor.execute("PRAGMA table_info(items)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'quantity' not in columns:
            logging.error("Quantity column not found after migration")
            return False
        
        # Check that we can query the column
        cursor.execute('SELECT item, quantity FROM items LIMIT 1')
        logging.info("Migration validation successful")
        return True
        
    except sqlite3.Error as e:
        logging.error(f"Migration validation failed: {e}")
        return False
    finally:
        conn.close()

def main():
    """Main migration function"""
    db_paths = ['nesop_store.db', 'nesop_store_production.db']
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            logging.info(f"Migrating database: {db_path}")
            
            # Perform migration
            if migrate_add_quantity_column(db_path):
                # Validate migration
                if validate_migration(db_path):
                    logging.info(f"Successfully migrated {db_path}")
                else:
                    logging.error(f"Migration validation failed for {db_path}")
                    sys.exit(1)
            else:
                logging.error(f"Migration failed for {db_path}")
                sys.exit(1)
        else:
            logging.info(f"Database {db_path} not found, skipping")
    
    logging.info("All database migrations completed successfully")

if __name__ == "__main__":
    main() 