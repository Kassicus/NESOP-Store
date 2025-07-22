#!/usr/bin/env python3
"""
NESOP Store - Fix Image Ownership Script
Fixes ownership of existing images that were uploaded with incorrect permissions.
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

def fix_image_ownership(app_root="/opt/nesop-store"):
    """Fix ownership for existing uploaded images"""
    logger = setup_logging()
    
    # Define paths
    app_root = Path(app_root)
    images_dir = app_root / "assets" / "images"
    
    logger.info(f"Fixing image ownership for NESOP Store at: {app_root}")
    logger.info(f"Images directory: {images_dir}")
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        return False
    
    # Check if images directory exists
    if not images_dir.exists():
        logger.error(f"Images directory not found: {images_dir}")
        return False
    
    # Try to get user and group IDs
    try:
        nesop_uid = pwd.getpwnam('nesop').pw_uid
        logger.info("Found nesop user")
    except KeyError:
        logger.error("nesop user not found - this is required for production deployment")
        return False
    
    # Get web server group ID (prefer www-data, fallback to nginx, then nesop)
    web_gid = None
    web_group = None
    for group_name in ['www-data', 'nginx', 'nesop']:
        try:
            web_gid = grp.getgrnam(group_name).gr_gid
            web_group = group_name
            logger.info(f"Found {group_name} group")
            break
        except KeyError:
            continue
    
    if web_gid is None:
        logger.error("No suitable web server group found (www-data, nginx, or nesop)")
        return False
    
    # Find and fix image files
    fixed_count = 0
    error_count = 0
    
    try:
        logger.info("Scanning for image files...")
        
        # Common image extensions
        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
        
        for file_path in images_dir.iterdir():
            if file_path.is_file():
                # Check if it's an image file
                if file_path.suffix.lower() in image_extensions:
                    try:
                        # Get current ownership
                        current_stat = file_path.stat()
                        current_uid = current_stat.st_uid
                        current_gid = current_stat.st_gid
                        
                        # Get current user/group names for logging
                        try:
                            current_user = pwd.getpwuid(current_uid).pw_name
                        except KeyError:
                            current_user = str(current_uid)
                        
                        try:
                            current_group = grp.getgrgid(current_gid).gr_name
                        except KeyError:
                            current_group = str(current_gid)
                        
                        logger.info(f"Processing: {file_path.name} (currently {current_user}:{current_group})")
                        
                        # Set correct ownership: nesop user, web server group
                        os.chown(file_path, nesop_uid, web_gid)
                        
                        # Set correct permissions: 664 (rw for owner and group, r for others)
                        os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
                        
                        logger.info(f"  ✓ Fixed: {file_path.name} → nesop:{web_group} (664)")
                        fixed_count += 1
                        
                    except Exception as e:
                        logger.error(f"  ✗ Failed to fix {file_path.name}: {e}")
                        error_count += 1
                else:
                    logger.debug(f"Skipping non-image file: {file_path.name}")
        
        logger.info("=" * 50)
        logger.info("IMAGE OWNERSHIP FIX COMPLETE!")
        logger.info("=" * 50)
        logger.info(f"✓ Files fixed: {fixed_count}")
        logger.info(f"✗ Errors: {error_count}")
        logger.info(f"✓ Owner: nesop")
        logger.info(f"✓ Group: {web_group}")
        logger.info(f"✓ Permissions: 664 (rw-rw-r--)")
        
        if error_count == 0:
            logger.info("\nAll images have been fixed successfully!")
            logger.info("Future uploads will automatically have correct ownership.")
        else:
            logger.warning(f"\n{error_count} files had errors. Check logs above for details.")
        
        return error_count == 0
        
    except Exception as e:
        logger.error(f"Failed to fix image ownership: {e}")
        return False

def list_image_ownership(app_root="/opt/nesop-store"):
    """List current ownership of image files"""
    logger = setup_logging()
    
    images_dir = Path(app_root) / "assets" / "images"
    
    if not images_dir.exists():
        logger.error(f"Images directory not found: {images_dir}")
        return
    
    logger.info("Current image file ownership:")
    logger.info("=" * 50)
    
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff'}
    
    for file_path in images_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in image_extensions:
            try:
                file_stat = file_path.stat()
                uid = file_stat.st_uid
                gid = file_stat.st_gid
                
                # Get user/group names
                try:
                    user_name = pwd.getpwuid(uid).pw_name
                except KeyError:
                    user_name = str(uid)
                
                try:
                    group_name = grp.getgrgid(gid).gr_name
                except KeyError:
                    group_name = str(gid)
                
                # Get permissions
                permissions = oct(file_stat.st_mode)[-3:]
                
                logger.info(f"{file_path.name:<30} {user_name}:{group_name:<15} {permissions}")
                
            except Exception as e:
                logger.error(f"Error reading {file_path.name}: {e}")

def main():
    """Main function"""
    logger = setup_logging()
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1]
        app_root = sys.argv[2] if len(sys.argv) > 2 else "/opt/nesop-store"
    else:
        command = "fix"
        app_root = "/opt/nesop-store"
    
    logger.info("NESOP Store Image Ownership Fix Script")
    logger.info("=" * 40)
    
    if command == "list":
        list_image_ownership(app_root)
    elif command == "fix":
        if fix_image_ownership(app_root):
            logger.info("Image ownership fix completed successfully!")
            logger.info("\nRecommended next steps:")
            logger.info("1. Restart the NESOP Store service:")
            logger.info("   sudo systemctl restart nesop-store")
            logger.info("2. Test image uploads to verify ownership is correct")
            sys.exit(0)
        else:
            logger.error("Image ownership fix failed!")
            sys.exit(1)
    else:
        logger.error(f"Unknown command: {command}")
        logger.info("Usage:")
        logger.info("  python3 fix_image_ownership.py [fix|list] [/path/to/nesop-store]")
        logger.info("Examples:")
        logger.info("  python3 fix_image_ownership.py fix")
        logger.info("  python3 fix_image_ownership.py list")
        logger.info("  python3 fix_image_ownership.py fix /opt/nesop-store")
        sys.exit(1)

if __name__ == "__main__":
    main() 