#!/usr/bin/env python3
"""
NESOP Store - Fix Assets Ownership
Fixes the specific ownership issue where assets directory is owned by root instead of nesop.
"""

import os
import stat
import sys
import logging
import grp
import pwd
import subprocess
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def fix_assets_ownership():
    """Fix the assets directory ownership issue"""
    logger = setup_logging()
    
    logger.info("NESOP Store - Fix Assets Ownership")
    logger.info("=" * 50)
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        return False
    
    # Define paths
    app_root = Path("/opt/nesop-store")
    assets_dir = app_root / "assets"
    images_dir = assets_dir / "images"
    
    # Get nesop user info
    try:
        nesop_user = pwd.getpwnam('nesop')
        nesop_uid = nesop_user.pw_uid
        logger.info(f"✓ Found nesop user (UID: {nesop_uid})")
    except KeyError:
        logger.error("✗ nesop user not found")
        return False
    
    # Get www-data group info
    try:
        www_data_group = grp.getgrnam('www-data')
        www_data_gid = www_data_group.gr_gid
        logger.info(f"✓ Found www-data group (GID: {www_data_gid})")
    except KeyError:
        logger.error("✗ www-data group not found")
        return False
    
    logger.info("")
    logger.info("Current ownership status:")
    
    # Check current ownership
    for name, path in [("Assets Dir", assets_dir), ("Images Dir", images_dir)]:
        if path.exists():
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
            
            logger.info(f"  {name}: {owner_name}:{group_name} ({permissions})")
        else:
            logger.info(f"  {name}: Does not exist")
    
    logger.info("")
    logger.info("Fixing ownership...")
    
    try:
        # Create directories if they don't exist
        assets_dir.mkdir(exist_ok=True)
        images_dir.mkdir(exist_ok=True)
        logger.info("✓ Directories created/verified")
        
        # Fix ownership recursively for assets directory
        for root, dirs, files in os.walk(assets_dir):
            root_path = Path(root)
            
            # Set directory ownership
            os.chown(root_path, nesop_uid, www_data_gid)
            
            # Set directory permissions: 775
            os.chmod(root_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
            
            # Set file ownership and permissions
            for file in files:
                file_path = root_path / file
                os.chown(file_path, nesop_uid, www_data_gid)
                # Set file permissions: 664
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
        
        logger.info("✓ Fixed ownership: nesop:www-data")
        logger.info("✓ Fixed permissions: directories 775, files 664")
        
        # Test write access
        logger.info("")
        logger.info("Testing write access...")
        
        test_file = images_dir / "ownership_test.tmp"
        try:
            # Test as nesop user
            result = subprocess.run(['sudo', '-u', 'nesop', 'touch', str(test_file)], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info("✓ nesop user can now write to images directory")
                # Clean up test file
                test_file.unlink()
            else:
                logger.error(f"✗ nesop user still cannot write: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"✗ Error testing write access: {e}")
            return False
        
        logger.info("")
        logger.info("=" * 50)
        logger.info("OWNERSHIP FIX COMPLETE!")
        logger.info("=" * 50)
        logger.info("✓ Assets directory: nesop:www-data (775)")
        logger.info("✓ Images directory: nesop:www-data (775)")
        logger.info("✓ Write test: PASSED")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Restart the NESOP Store service:")
        logger.info("   sudo systemctl restart nesop-store")
        logger.info("2. Test image upload - it should work now!")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Error fixing ownership: {e}")
        return False

def main():
    """Main function"""
    logger = setup_logging()
    
    if fix_assets_ownership():
        logger.info("\n🎉 Assets ownership fixed successfully!")
        logger.info("Your upload permissions should now work correctly.")
        
        # Restart service automatically
        try:
            logger.info("Restarting nesop-store service...")
            result = subprocess.run(['systemctl', 'restart', 'nesop-store'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("✓ Service restarted successfully")
            else:
                logger.warning(f"⚠️  Service restart failed: {result.stderr}")
                logger.info("Please restart manually: sudo systemctl restart nesop-store")
        except Exception as e:
            logger.warning(f"⚠️  Could not restart service: {e}")
            logger.info("Please restart manually: sudo systemctl restart nesop-store")
        
        sys.exit(0)
    else:
        logger.error("\n❌ Failed to fix assets ownership!")
        sys.exit(1)

if __name__ == "__main__":
    main() 