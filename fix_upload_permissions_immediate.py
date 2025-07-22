#!/usr/bin/env python3
"""
NESOP Store - Immediate Upload Permission Fix
Fixes the immediate permission error preventing image uploads.
"""

import os
import stat
import sys
import logging
import grp
import pwd
from pathlib import Path
import subprocess

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def fix_upload_permissions_immediate(app_root="/opt/nesop-store"):
    """Fix upload permissions immediately to resolve the current error"""
    logger = setup_logging()
    
    logger.info("NESOP Store - Immediate Upload Permission Fix")
    logger.info("=" * 50)
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        logger.info("Usage: sudo python3 fix_upload_permissions_immediate.py")
        return False
    
    # Define paths
    app_root = Path(app_root)
    assets_dir = app_root / "assets"
    images_dir = assets_dir / "images"
    
    logger.info(f"Application root: {app_root}")
    logger.info(f"Assets directory: {assets_dir}")
    logger.info(f"Images directory: {images_dir}")
    logger.info("")
    
    # Get user and group IDs
    try:
        nesop_uid = pwd.getpwnam('nesop').pw_uid
        logger.info("✓ Found nesop user")
    except KeyError:
        logger.error("✗ nesop user not found - creating it...")
        try:
            subprocess.run(['useradd', '-r', '-s', '/bin/false', 'nesop'], check=True)
            nesop_uid = pwd.getpwnam('nesop').pw_uid
            logger.info("✓ Created nesop user")
        except Exception as e:
            logger.error(f"✗ Failed to create nesop user: {e}")
            return False
    
    # Get web server group
    web_gid = None
    web_group = None
    for group_name in ['www-data', 'nginx', 'nesop']:
        try:
            web_gid = grp.getgrnam(group_name).gr_gid
            web_group = group_name
            logger.info(f"✓ Using {group_name} group")
            break
        except KeyError:
            continue
    
    if web_gid is None:
        logger.error("✗ No suitable web server group found")
        return False
    
    try:
        # Step 1: Create directories if they don't exist
        logger.info("1. Creating/verifying directories...")
        assets_dir.mkdir(exist_ok=True)
        images_dir.mkdir(exist_ok=True)
        logger.info("   ✓ Directories created/verified")
        
        # Step 2: Set ownership for the entire assets directory
        logger.info("2. Setting ownership...")
        for root, dirs, files in os.walk(assets_dir):
            root_path = Path(root)
            os.chown(root_path, nesop_uid, web_gid)
            
            for file in files:
                file_path = root_path / file
                os.chown(file_path, nesop_uid, web_gid)
        
        logger.info(f"   ✓ Set ownership to nesop:{web_group}")
        
        # Step 3: Set permissions
        logger.info("3. Setting permissions...")
        
        # Set directory permissions: 775 (rwx for owner and group, r-x for others)
        for root, dirs, files in os.walk(assets_dir):
            root_path = Path(root)
            os.chmod(root_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
            
            # Set file permissions: 664 (rw for owner and group, r for others)
            for file in files:
                file_path = root_path / file
                os.chmod(file_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH)
        
        logger.info("   ✓ Set permissions: directories 775, files 664")
        
        # Step 4: Test write access
        logger.info("4. Testing write access...")
        test_file = images_dir / "permission_test.tmp"
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            test_file.unlink()
            logger.info("   ✓ Write test successful")
        except Exception as e:
            logger.error(f"   ✗ Write test failed: {e}")
            return False
        
        # Step 5: Check service user context
        logger.info("5. Checking service configuration...")
        
        # Check what user the service runs as
        try:
            result = subprocess.run(['systemctl', 'show', 'nesop-store', '--property=User'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                service_user = result.stdout.strip().split('=')[1] if '=' in result.stdout else 'unknown'
                logger.info(f"   Service runs as user: {service_user}")
                
                if service_user != 'nesop':
                    logger.warning(f"   ⚠️  Service runs as '{service_user}' but files are owned by 'nesop'")
                    logger.info("   This might cause permission issues.")
                    
                    # Add service user to web server group
                    if service_user not in ['unknown', '']:
                        try:
                            subprocess.run(['usermod', '-a', '-G', web_group, service_user], check=True)
                            logger.info(f"   ✓ Added {service_user} to {web_group} group")
                        except Exception as e:
                            logger.warning(f"   ⚠️  Could not add {service_user} to {web_group}: {e}")
            
        except Exception as e:
            logger.warning(f"   ⚠️  Could not check service user: {e}")
        
        logger.info("")
        logger.info("=" * 50)
        logger.info("IMMEDIATE FIX COMPLETE!")
        logger.info("=" * 50)
        logger.info(f"✓ Assets directory: {assets_dir}")
        logger.info(f"✓ Images directory: {images_dir}")
        logger.info(f"✓ Ownership: nesop:{web_group}")
        logger.info(f"✓ Directory permissions: 775")
        logger.info(f"✓ File permissions: 664")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Restart the NESOP Store service:")
        logger.info("   sudo systemctl restart nesop-store")
        logger.info("2. Test image upload in the admin panel")
        logger.info("3. If issues persist, check service logs:")
        logger.info("   sudo journalctl -u nesop-store -f")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to fix permissions: {e}")
        return False

def main():
    """Main function"""
    logger = setup_logging()
    
    app_root = sys.argv[1] if len(sys.argv) > 1 else "/opt/nesop-store"
    
    if fix_upload_permissions_immediate(app_root):
        logger.info("\n🎉 Upload permissions fixed successfully!")
        logger.info("You should now be able to upload images.")
        sys.exit(0)
    else:
        logger.error("\n❌ Failed to fix upload permissions!")
        logger.info("Please check the error messages above and try manual fixes.")
        sys.exit(1)

if __name__ == "__main__":
    main() 