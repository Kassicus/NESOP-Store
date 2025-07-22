#!/usr/bin/env python3
"""
NESOP Store - Upload Permissions Diagnostic Script
Checks and diagnoses upload directory permission issues.
"""

import os
import stat
import sys
import logging
import grp
import pwd
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def check_upload_permissions(app_root="/opt/nesop-store"):
    """Check upload directory permissions and identify issues"""
    logger = setup_logging()
    
    # Define paths
    app_root = Path(app_root)
    assets_dir = app_root / "assets"
    images_dir = assets_dir / "images"
    
    logger.info("NESOP Store Upload Permissions Diagnostic")
    logger.info("=" * 50)
    logger.info(f"Application root: {app_root}")
    logger.info(f"Assets directory: {assets_dir}")
    logger.info(f"Images directory: {images_dir}")
    logger.info("")
    
    # Check if directories exist
    logger.info("1. Directory Existence Check:")
    for name, path in [("App Root", app_root), ("Assets", assets_dir), ("Images", images_dir)]:
        if path.exists():
            logger.info(f"   ✓ {name}: {path} exists")
        else:
            logger.error(f"   ✗ {name}: {path} does not exist")
    logger.info("")
    
    # Check current user context
    logger.info("2. Current Process Context:")
    current_uid = os.getuid()
    current_gid = os.getgid()
    
    try:
        current_user = pwd.getpwuid(current_uid).pw_name
    except KeyError:
        current_user = str(current_uid)
    
    try:
        current_group = grp.getgrgid(current_gid).gr_name
    except KeyError:
        current_group = str(current_gid)
    
    logger.info(f"   Current user: {current_user} (UID: {current_uid})")
    logger.info(f"   Current group: {current_group} (GID: {current_gid})")
    logger.info(f"   Running as root: {'Yes' if current_uid == 0 else 'No'}")
    logger.info("")
    
    # Check directory ownership and permissions
    logger.info("3. Directory Ownership and Permissions:")
    for name, path in [("App Root", app_root), ("Assets", assets_dir), ("Images", images_dir)]:
        if path.exists():
            try:
                stat_info = path.stat()
                owner_uid = stat_info.st_uid
                owner_gid = stat_info.st_gid
                permissions = oct(stat_info.st_mode)[-3:]
                
                try:
                    owner_name = pwd.getpwuid(owner_uid).pw_name
                except KeyError:
                    owner_name = str(owner_uid)
                
                try:
                    group_name = grp.getgrgid(owner_gid).gr_name
                except KeyError:
                    group_name = str(owner_gid)
                
                logger.info(f"   {name}:")
                logger.info(f"     Owner: {owner_name}:{group_name} ({owner_uid}:{owner_gid})")
                logger.info(f"     Permissions: {permissions}")
                
                # Check if current user can write
                if path.is_dir():
                    can_write = os.access(path, os.W_OK)
                    logger.info(f"     Writable by current user: {'Yes' if can_write else 'No'}")
                
            except Exception as e:
                logger.error(f"   Error checking {name}: {e}")
    logger.info("")
    
    # Check specific write test
    logger.info("4. Write Permission Test:")
    if images_dir.exists():
        test_file = images_dir / "permission_test.tmp"
        try:
            # Try to create a test file
            with open(test_file, 'w') as f:
                f.write("test")
            
            # If successful, remove it
            test_file.unlink()
            logger.info("   ✓ Can write to images directory")
            
        except PermissionError as e:
            logger.error(f"   ✗ Cannot write to images directory: {e}")
        except Exception as e:
            logger.error(f"   ✗ Write test failed: {e}")
    else:
        logger.error("   ✗ Images directory does not exist")
    logger.info("")
    
    # Check service user information
    logger.info("5. Service User Information:")
    try:
        nesop_user = pwd.getpwnam('nesop')
        logger.info(f"   nesop user exists: UID {nesop_user.pw_uid}, GID {nesop_user.pw_gid}")
        logger.info(f"   nesop home: {nesop_user.pw_dir}")
        logger.info(f"   nesop shell: {nesop_user.pw_shell}")
    except KeyError:
        logger.error("   ✗ nesop user does not exist")
    
    # Check web server groups
    logger.info("   Web server groups:")
    for group_name in ['www-data', 'nginx', 'nesop']:
        try:
            group_info = grp.getgrnam(group_name)
            logger.info(f"     {group_name}: GID {group_info.gr_gid}, Members: {group_info.gr_mem}")
        except KeyError:
            logger.info(f"     {group_name}: Not found")
    logger.info("")
    
    # Provide recommendations
    logger.info("6. Recommendations:")
    
    if not images_dir.exists():
        logger.info("   • Create images directory:")
        logger.info("     sudo mkdir -p /opt/nesop-store/assets/images")
    
    if images_dir.exists() and not os.access(images_dir, os.W_OK):
        logger.info("   • Fix directory permissions:")
        logger.info("     sudo chown -R nesop:www-data /opt/nesop-store/assets/")
        logger.info("     sudo chmod -R 775 /opt/nesop-store/assets/")
        logger.info("     sudo systemctl restart nesop-store")
    
    logger.info("   • Run the comprehensive permission fix:")
    logger.info("     sudo python3 /opt/nesop-store/fix_permissions.py")
    
    logger.info("   • Or run the image-specific fix:")
    logger.info("     sudo python3 /opt/nesop-store/fix_image_ownership.py fix")

def main():
    """Main function"""
    app_root = sys.argv[1] if len(sys.argv) > 1 else "/opt/nesop-store"
    check_upload_permissions(app_root)

if __name__ == "__main__":
    main() 