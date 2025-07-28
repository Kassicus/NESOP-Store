#!/usr/bin/env python3
"""
Migration script to fix items table schema inconsistency

This migration addresses the database schema mismatch where some deployments 
may have created the items table with incorrect column names, causing image 
references to not be stored or retrieved properly.

Issue: validate_deployment.py was creating items table with:
- 'name' instead of 'item' 
- 'id' as primary key instead of 'item'
- Missing 'sold_out', 'unlisted', 'quantity' columns

This migration will:
1. Check current schema
2. Migrate data if old schema is detected
3. Ensure correct schema for proper image handling
"""

import sqlite3
import os
import logging
import sys
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_database_path():
    """Get the production database path"""
    # Try to get from environment first
    db_path = os.getenv('DB_PATH')
    if db_path and os.path.exists(db_path):
        return db_path
    
    # Look for production database
    production_db = 'nesop_store_production.db'
    if os.path.exists(production_db):
        return production_db
    
    # Fall back to development database
    dev_db = 'nesop_store.db'
    if os.path.exists(dev_db):
        return dev_db
    
    raise FileNotFoundError("No database file found")

def check_current_schema(cursor):
    """Check the current items table schema"""
    try:
        cursor.execute("PRAGMA table_info(items)")
        columns = cursor.fetchall()
        column_info = {col[1]: col for col in columns}  # col[1] is column name
        
        logger.info("Current items table schema:")
        for col in columns:
            logger.info(f"  - {col[1]} {col[2]} (PK: {bool(col[5])}, NotNull: {bool(col[3])}, Default: {col[4]})")
        
        return column_info
    except sqlite3.Error as e:
        logger.error(f"Error checking schema: {e}")
        return None

def needs_migration(column_info):
    """Determine if migration is needed"""
    # Check for old schema indicators
    has_name_column = 'name' in column_info
    has_item_column = 'item' in column_info
    has_id_pk = 'id' in column_info and column_info['id'][5] == 1  # col[5] is primary key flag
    
    # If has 'name' column but no 'item' column, needs migration
    if has_name_column and not has_item_column:
        logger.info("Migration needed: Old schema detected with 'name' column instead of 'item'")
        return True
    
    # If has 'id' as primary key, might need migration
    if has_id_pk and not has_item_column:
        logger.info("Migration needed: Old schema detected with 'id' as primary key")
        return True
    
    # Check for missing columns
    expected_columns = ['item', 'description', 'price', 'image', 'sold_out', 'unlisted', 'quantity']
    missing_columns = [col for col in expected_columns if col not in column_info]
    
    if missing_columns:
        logger.info(f"Migration needed: Missing columns: {missing_columns}")
        return True
    
    logger.info("No migration needed: Schema is correct")
    return False

def backup_table(cursor, backup_name="items_backup"):
    """Create a backup of the current items table"""
    try:
        cursor.execute(f"DROP TABLE IF EXISTS {backup_name}")
        cursor.execute(f"CREATE TABLE {backup_name} AS SELECT * FROM items")
        cursor.execute(f"SELECT COUNT(*) FROM {backup_name}")
        count = cursor.fetchone()[0]
        logger.info(f"✓ Backup table '{backup_name}' created with {count} records")
        return True
    except sqlite3.Error as e:
        logger.error(f"Failed to create backup: {e}")
        return False

def migrate_schema_old_to_new(cursor):
    """Migrate from old schema to new schema"""
    try:
        # First, backup the existing data
        if not backup_table(cursor):
            return False
        
        # Get existing data
        cursor.execute("SELECT * FROM items")
        existing_data = cursor.fetchall()
        
        # Get column info to understand the old structure
        cursor.execute("PRAGMA table_info(items)")
        old_columns = cursor.fetchall()
        old_column_names = [col[1] for col in old_columns]
        
        logger.info(f"Migrating {len(existing_data)} records from old schema")
        logger.info(f"Old columns: {old_column_names}")
        
        # Create new table with correct schema
        cursor.execute("""
            CREATE TABLE items_new (
                item TEXT PRIMARY KEY,
                description TEXT,
                price REAL,
                image TEXT,
                sold_out INTEGER DEFAULT 0,
                unlisted INTEGER DEFAULT 0,
                quantity INTEGER DEFAULT 0
            )
        """)
        
        # Migrate data based on old schema
        if 'name' in old_column_names:
            # Old schema with 'name' column
            for row in existing_data:
                row_dict = dict(zip(old_column_names, row))
                
                item = row_dict.get('name', 'Unknown Item')
                description = row_dict.get('description', '')
                price = row_dict.get('price', 0.0)
                image = row_dict.get('image', None)
                sold_out = row_dict.get('sold_out', 0)
                unlisted = row_dict.get('unlisted', 0)
                quantity = row_dict.get('quantity', 0)
                
                cursor.execute("""
                    INSERT INTO items_new (item, description, price, image, sold_out, unlisted, quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (item, description, price, image, sold_out, unlisted, quantity))
        else:
            # Try to map whatever columns exist
            for row in existing_data:
                row_dict = dict(zip(old_column_names, row))
                
                # Try to find the item name in various possible columns
                item = row_dict.get('item') or row_dict.get('name') or f"Item_{row_dict.get('id', 'Unknown')}"
                description = row_dict.get('description', '')
                price = row_dict.get('price', 0.0)
                image = row_dict.get('image', None)
                sold_out = row_dict.get('sold_out', 0)
                unlisted = row_dict.get('unlisted', 0)
                quantity = row_dict.get('quantity', 0)
                
                cursor.execute("""
                    INSERT INTO items_new (item, description, price, image, sold_out, unlisted, quantity)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (item, description, price, image, sold_out, unlisted, quantity))
        
        # Drop old table and rename new table
        cursor.execute("DROP TABLE items")
        cursor.execute("ALTER TABLE items_new RENAME TO items")
        
        # Verify migration
        cursor.execute("SELECT COUNT(*) FROM items")
        new_count = cursor.fetchone()[0]
        
        logger.info(f"✓ Schema migration completed successfully")
        logger.info(f"✓ Migrated {new_count} records to new schema")
        
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Migration failed: {e}")
        # Try to restore from backup if possible
        try:
            cursor.execute("DROP TABLE IF EXISTS items")
            cursor.execute("ALTER TABLE items_backup RENAME TO items")
            logger.info("✓ Restored from backup after migration failure")
        except:
            logger.error("Could not restore from backup")
        return False

def add_missing_columns(cursor, column_info):
    """Add missing columns to existing correct schema"""
    expected_columns = {
        'sold_out': 'INTEGER DEFAULT 0',
        'unlisted': 'INTEGER DEFAULT 0', 
        'quantity': 'INTEGER DEFAULT 0'
    }
    
    for col_name, col_def in expected_columns.items():
        if col_name not in column_info:
            try:
                cursor.execute(f"ALTER TABLE items ADD COLUMN {col_name} {col_def}")
                logger.info(f"✓ Added missing column: {col_name}")
            except sqlite3.Error as e:
                logger.error(f"Failed to add column {col_name}: {e}")
                return False
    
    return True

def validate_final_schema(cursor):
    """Validate the final schema is correct"""
    try:
        cursor.execute("PRAGMA table_info(items)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        expected_columns = ['item', 'description', 'price', 'image', 'sold_out', 'unlisted', 'quantity']
        
        missing = [col for col in expected_columns if col not in column_names]
        if missing:
            logger.error(f"Validation failed: Missing columns: {missing}")
            return False
        
        # Check primary key
        pk_columns = [col[1] for col in columns if col[5] == 1]  # col[5] is primary key flag
        if pk_columns != ['item']:
            logger.error(f"Validation failed: Expected 'item' as primary key, got: {pk_columns}")
            return False
        
        logger.info("✓ Final schema validation passed")
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Schema validation error: {e}")
        return False

def main():
    """Main migration function"""
    logger.info("Starting items table schema migration...")
    
    try:
        # Get database path
        db_path = get_database_path()
        logger.info(f"Using database: {db_path}")
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if items table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items'")
        if not cursor.fetchone():
            logger.info("Items table does not exist - nothing to migrate")
            return True
        
        # Check current schema
        column_info = check_current_schema(cursor)
        if not column_info:
            logger.error("Could not read current schema")
            return False
        
        # Determine if migration is needed
        if not needs_migration(column_info):
            logger.info("No migration needed - schema is already correct")
            return True
        
        # Perform migration
        logger.info("Starting schema migration...")
        
        # Begin transaction
        cursor.execute("BEGIN TRANSACTION")
        
        try:
            # Check if this is a complete schema change or just missing columns
            if 'name' in column_info or ('id' in column_info and column_info['id'][5] == 1):
                # Complete schema migration needed
                success = migrate_schema_old_to_new(cursor)
            else:
                # Just add missing columns
                success = add_missing_columns(cursor, column_info)
            
            if not success:
                cursor.execute("ROLLBACK")
                logger.error("Migration failed - rolled back changes")
                return False
            
            # Validate final schema
            if not validate_final_schema(cursor):
                cursor.execute("ROLLBACK")
                logger.error("Schema validation failed - rolled back changes")
                return False
            
            # Commit changes
            cursor.execute("COMMIT")
            logger.info("✓ Migration completed successfully")
            
            # Show final status
            cursor.execute("SELECT COUNT(*) FROM items")
            item_count = cursor.fetchone()[0]
            logger.info(f"✓ Items table now has {item_count} records with correct schema")
            
            return True
            
        except Exception as e:
            cursor.execute("ROLLBACK")
            logger.error(f"Migration failed with error: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Migration error: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 