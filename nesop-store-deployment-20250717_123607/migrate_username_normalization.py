#!/usr/bin/env python3
"""
Database migration script to normalize usernames and merge duplicate users.

This script addresses the issue where users could be created with different
username formats (e.g., "username" vs "username@domain.com") representing
the same person.

The script will:
1. Identify potential duplicate users based on normalized usernames
2. Merge user data (keeping the highest balance and admin status)
3. Update all related records (purchases, reviews) to use the normalized username
4. Remove duplicate user entries

Run this script after updating the application code to use normalized usernames.
"""

import sqlite3
import logging
from datetime import datetime
import sys
import os

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ad_utils
import db_utils

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('username_migration.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_normalized_username_groups(conn):
    """
    Get groups of users that would normalize to the same username.
    
    Returns:
        dict: Dictionary mapping normalized username to list of original usernames
    """
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE is_active = 1')
    users = cursor.fetchall()
    
    normalized_groups = {}
    for user in users:
        original_username = user[0]
        normalized_username = ad_utils.ActiveDirectoryManager.normalize_username(original_username)
        
        if normalized_username not in normalized_groups:
            normalized_groups[normalized_username] = []
        normalized_groups[normalized_username].append(original_username)
    
    # Filter to only return groups with duplicates
    duplicate_groups = {k: v for k, v in normalized_groups.items() if len(v) > 1}
    
    return duplicate_groups

def merge_user_data(conn, usernames_to_merge, target_username):
    """
    Merge data from multiple user records into a single normalized user.
    
    Args:
        conn: Database connection
        usernames_to_merge: List of usernames to merge
        target_username: The normalized username to keep
    """
    cursor = conn.cursor()
    
    # Get all user data to merge
    user_data = []
    for username in usernames_to_merge:
        cursor.execute('''
            SELECT username, password, balance, is_admin, user_type, 
                   ad_username, ad_domain, ad_display_name, ad_email, 
                   last_ad_sync, is_active, created_at, updated_at 
            FROM users 
            WHERE username = ?
        ''', (username,))
        user = cursor.fetchone()
        if user:
            user_data.append(user)
    
    if not user_data:
        logger.warning(f"No user data found for usernames: {usernames_to_merge}")
        return
    
    # Determine the best data to keep
    # Keep the highest balance, admin status if any user has it, latest AD sync
    merged_data = {
        'username': target_username,
        'password': user_data[0][1],  # Keep first password (they should be the same for AD users)
        'balance': max(user[2] for user in user_data),  # Highest balance
        'is_admin': max(user[3] for user in user_data),  # Admin if any user is admin
        'user_type': user_data[0][4],  # Keep first user type
        'ad_username': user_data[0][5],  # Keep first AD username
        'ad_domain': user_data[0][6],  # Keep first AD domain
        'ad_display_name': user_data[0][7],  # Keep first AD display name
        'ad_email': user_data[0][8],  # Keep first AD email
        'last_ad_sync': max((user[9] for user in user_data if user[9]), default=None),  # Latest sync
        'is_active': 1,
        'created_at': min(user[11] for user in user_data if user[11]),  # Earliest creation
        'updated_at': datetime.now().isoformat()
    }
    
    logger.info(f"Merging users {usernames_to_merge} into {target_username}")
    logger.info(f"Merged balance: {merged_data['balance']}, admin: {merged_data['is_admin']}")
    
    # Update related records first
    for old_username in usernames_to_merge:
        if old_username != target_username:
            # Update purchases
            cursor.execute('''
                UPDATE purchases 
                SET username = ? 
                WHERE username = ?
            ''', (target_username, old_username))
            
            # Update reviews
            cursor.execute('''
                UPDATE reviews 
                SET username = ? 
                WHERE username = ?
            ''', (target_username, old_username))
            
            logger.info(f"Updated related records for {old_username} -> {target_username}")
    
    # Delete old user records
    for old_username in usernames_to_merge:
        cursor.execute('DELETE FROM users WHERE username = ?', (old_username,))
        logger.info(f"Deleted old user record: {old_username}")
    
    # Insert merged user record
    cursor.execute('''
        INSERT INTO users (
            username, password, balance, is_admin, user_type, 
            ad_username, ad_domain, ad_display_name, ad_email, 
            last_ad_sync, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        merged_data['username'], merged_data['password'], merged_data['balance'],
        merged_data['is_admin'], merged_data['user_type'], merged_data['ad_username'],
        merged_data['ad_domain'], merged_data['ad_display_name'], merged_data['ad_email'],
        merged_data['last_ad_sync'], merged_data['is_active'], 
        merged_data['created_at'], merged_data['updated_at']
    ))
    
    logger.info(f"Created merged user record: {target_username}")

def main():
    """Main migration function"""
    logger.info("Starting username normalization migration")
    
    # Get database connection
    conn = db_utils.get_db_connection()
    
    try:
        # Create backup
        backup_filename = f"users_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        logger.info(f"Creating backup: {backup_filename}")
        
        with open(backup_filename, 'w') as f:
            for line in conn.iterdump():
                f.write('%s\n' % line)
        
        logger.info("Backup created successfully")
        
        # Find duplicate groups
        duplicate_groups = get_normalized_username_groups(conn)
        
        if not duplicate_groups:
            logger.info("No duplicate users found. Migration not needed.")
            return
        
        logger.info(f"Found {len(duplicate_groups)} groups of duplicate users:")
        for normalized, originals in duplicate_groups.items():
            logger.info(f"  {normalized}: {originals}")
        
        # Confirm migration
        response = input("\nProceed with migration? (y/N): ")
        if response.lower() != 'y':
            logger.info("Migration cancelled by user")
            return
        
        # Begin transaction
        conn.execute('BEGIN TRANSACTION')
        
        # Merge duplicate users
        for normalized_username, original_usernames in duplicate_groups.items():
            merge_user_data(conn, original_usernames, normalized_username)
        
        # Commit transaction
        conn.commit()
        
        logger.info("Migration completed successfully")
        
        # Verify results
        logger.info("Verification:")
        remaining_duplicates = get_normalized_username_groups(conn)
        if remaining_duplicates:
            logger.warning(f"Still have duplicates: {remaining_duplicates}")
        else:
            logger.info("No duplicate users remaining")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    main() 