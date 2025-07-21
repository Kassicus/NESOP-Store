#!/usr/bin/env python3
"""
NESOP Store - Permission Fix Script
Fixes file upload permissions for production deployments
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

def fix_upload_permissions(app_root="/opt/nesop-store"):
    """Fix permissions for the upload directory"""
    logger = setup_logging()
    
    # Define paths
    app_root = Path(app_root)
    assets_dir = app_root / "assets"
    images_dir = assets_dir / "images"
    
    logger.info(f"Fixing permissions for NESOP Store at: {app_root}")
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        return False
    
    # Check if application directory exists
    if not app_root.exists():
        logger.error(f"Application directory not found: {app_root}")
        return False
    
    # Create directories if they don't exist
    try:
        assets_dir.mkdir(exist_ok=True)
        images_dir.mkdir(exist_ok=True)
        logger.info("Created/verified asset directories")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        return False
    
    # Try to get user and group IDs
    try:
        nesop_uid = pwd.getpwnam('nesop').pw_uid
        logger.info("Found nesop user")
    except KeyError:
        logger.warning("nesop user not found, using current user")
        nesop_uid = os.getuid()
    
    try:
        www_data_gid = grp.getgrnam('www-data').gr_gid
        web_group = 'www-data'
        logger.info("Found www-data group")
    except KeyError:
        try:
            # Try nginx group as fallback
            www_data_gid = grp.getgrnam('nginx').gr_gid
            web_group = 'nginx'
            logger.info("Found nginx group (using as web server group)")
        except KeyError:
            # Use nesop group as fallback
            try:
                www_data_gid = grp.getgrnam('nesop').gr_gid
                web_group = 'nesop'
                logger.warning("Using nesop group (no www-data or nginx found)")
            except KeyError:
                logger.error("No suitable web server group found")
                return False
    
    # Fix ownership and permissions
    try:
        # Set ownership for the entire application
        for root, dirs, files in os.walk(app_root):
            root_path = Path(root)
            
            # Set ownership: nesop user, web server group
            os.chown(root_path, nesop_uid, www_data_gid)
            
            # Set directory permissions
            if root_path.name in ['assets', 'images'] or 'assets' in root_path.parts:
                # Assets directory: 775 (rwx for owner and group, r-x for others)
                os.chmod(root_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
            else:
                # Other directories: 755 (rwx for owner, r-x for group and others)
                os.chmod(root_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            
            # Set file permissions
            for file in files:
                file_path = root_path / file
                os.chown(file_path, nesop_uid, www_data_gid)
                
                if 'assets' in root_path.parts:
                    # Asset files: 664 (rw for owner and group, r for others)
                    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
                else:
                    # Other files: 644 (rw for owner, r for group and others)
                    os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
        
        logger.info(f"Successfully fixed permissions:")
        logger.info(f"  - Owner: nesop")
        logger.info(f"  - Group: {web_group}")
        logger.info(f"  - Assets directory: 775 permissions")
        logger.info(f"  - Other directories: 755 permissions")
        logger.info(f"  - Asset files: 664 permissions")
        logger.info(f"  - Other files: 644 permissions")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to fix permissions: {e}")
        return False

def main():
    """Main function"""
    logger = setup_logging()
    
    # Get application root from command line or use default
    app_root = sys.argv[1] if len(sys.argv) > 1 else "/opt/nesop-store"
    
    logger.info("NESOP Store Permission Fix Script")
    logger.info("=" * 40)
    
    if fix_upload_permissions(app_root):
        logger.info("Permission fix completed successfully!")
        logger.info("You may need to restart your web server:")
        logger.info("  sudo systemctl restart nesop-store")
        logger.info("  sudo systemctl restart nginx")
        sys.exit(0)
    else:
        logger.error("Permission fix failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 