#!/usr/bin/env python3
"""
NESOP Store - Fix New Uploads Ownership
Fixes ownership of newly uploaded files that have incorrect ownership.
"""

import os
import stat
import sys
import logging
import grp
import pwd
from pathlib import Path
import time

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def fix_new_uploads_ownership():
    """Fix ownership of recently uploaded files"""
    logger = setup_logging()
    
    logger.info("NESOP Store - Fix New Uploads Ownership")
    logger.info("=" * 50)
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        return False
    
    images_dir = Path("/opt/nesop-store/assets/images")
    
    if not images_dir.exists():
        logger.error(f"Images directory not found: {images_dir}")
        return False
    
    # Get nesop and www-data IDs
    try:
        nesop_uid = pwd.getpwnam('nesop').pw_uid
        www_data_gid = grp.getgrnam('www-data').gr_gid
        logger.info(f"Target ownership: nesop:www-data ({nesop_uid}:{www_data_gid})")
    except KeyError as e:
        logger.error(f"User/group not found: {e}")
        return False
    
    # Find files with incorrect ownership
    logger.info("Scanning for files with incorrect ownership...")
    
    fixed_count = 0
    error_count = 0
    
    # Get files modified in the last hour (recent uploads)
    current_time = time.time()
    one_hour_ago = current_time - 3600  # 1 hour ago
    
    for file_path in images_dir.iterdir():
        if file_path.is_file():
            try:
                stat_info = file_path.stat()
                
                # Check if file was modified recently
                if stat_info.st_mtime > one_hour_ago:
                    owner_uid = stat_info.st_uid
                    owner_gid = stat_info.st_gid
                    
                    try:
                        owner_name = pwd.getpwuid(owner_uid).pw_name
                    except KeyError:
                        owner_name = str(owner_uid)
                    
                    try:
                        group_name = grp.getgrgid(owner_gid).gr_name
                    except KeyError:
                        group_name = str(owner_gid)
                    
                    logger.info(f"Recent file: {file_path.name}")
                    logger.info(f"  Current: {owner_name}:{group_name} ({owner_uid}:{owner_gid})")
                    
                    # Check if ownership needs fixing
                    if owner_uid != nesop_uid or owner_gid != www_data_gid:
                        try:
                            # Fix ownership
                            os.chown(file_path, nesop_uid, www_data_gid)
                            
                            # Set permissions
                            os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
                            
                            logger.info(f"  ✓ Fixed: {file_path.name} → nesop:www-data (664)")
                            fixed_count += 1
                            
                        except Exception as e:
                            logger.error(f"  ✗ Failed to fix {file_path.name}: {e}")
                            error_count += 1
                    else:
                        logger.info(f"  ✓ Already correct: {file_path.name}")
                        
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                error_count += 1
    
    logger.info("")
    logger.info("=" * 50)
    logger.info("OWNERSHIP FIX COMPLETE!")
    logger.info("=" * 50)
    logger.info(f"✓ Files fixed: {fixed_count}")
    logger.info(f"✗ Errors: {error_count}")
    
    return error_count == 0

def test_upload_ownership_function():
    """Test the upload ownership function from server.py"""
    logger = setup_logging()
    
    logger.info("Testing upload ownership function...")
    
    # Import the function from server.py
    sys.path.insert(0, '/opt/nesop-store')
    try:
        from server import set_file_ownership_and_permissions
        
        # Create a test file
        test_file = Path("/opt/nesop-store/assets/images/test_ownership.tmp")
        
        # Create test file as current user
        with open(test_file, 'w') as f:
            f.write("test")
        
        logger.info(f"Created test file: {test_file}")
        
        # Get initial ownership
        stat_info = test_file.stat()
        initial_uid = stat_info.st_uid
        initial_gid = stat_info.st_gid
        
        try:
            initial_user = pwd.getpwuid(initial_uid).pw_name
        except KeyError:
            initial_user = str(initial_uid)
        
        try:
            initial_group = grp.getgrgid(initial_gid).gr_name
        except KeyError:
            initial_group = str(initial_gid)
        
        logger.info(f"Initial ownership: {initial_user}:{initial_group}")
        
        # Test the function
        result = set_file_ownership_and_permissions(str(test_file))
        
        if result:
            # Check final ownership
            final_stat = test_file.stat()
            final_uid = final_stat.st_uid
            final_gid = final_stat.st_gid
            
            try:
                final_user = pwd.getpwuid(final_uid).pw_name
            except KeyError:
                final_user = str(final_uid)
            
            try:
                final_group = grp.getgrgid(final_gid).gr_name
            except KeyError:
                final_group = str(final_gid)
            
            logger.info(f"Final ownership: {final_user}:{final_group}")
            logger.info("✓ Ownership function test completed")
        else:
            logger.error("✗ Ownership function failed")
        
        # Clean up
        test_file.unlink()
        
    except Exception as e:
        logger.error(f"Error testing ownership function: {e}")

def main():
    """Main function"""
    logger = setup_logging()
    
    command = sys.argv[1] if len(sys.argv) > 1 else "fix"
    
    if command == "test":
        test_upload_ownership_function()
    elif command == "fix":
        if fix_new_uploads_ownership():
            logger.info("\n🎉 New uploads ownership fixed successfully!")
        else:
            logger.error("\n❌ Some files had errors during fixing!")
    else:
        logger.info("Usage:")
        logger.info("  python3 fix_new_uploads_ownership.py [fix|test]")
        logger.info("Commands:")
        logger.info("  fix  - Fix ownership of recently uploaded files")
        logger.info("  test - Test the upload ownership function")

if __name__ == "__main__":
    main() 