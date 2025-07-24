#!/usr/bin/env python3
"""
NESOP Store - Emergency Service Permission Fix
Quickly restores execute permissions for critical service files
"""

import os
import stat
import sys
import logging
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def fix_service_permissions(app_root="/opt/nesop-store"):
    """Emergency fix for service execution permissions"""
    logger = setup_logging()
    
    app_root = Path(app_root)
    logger.info(f"Emergency permission fix for: {app_root}")
    
    # Check if running as root
    if os.geteuid() != 0:
        logger.error("This script must be run as root (use sudo)")
        return False
    
    if not app_root.exists():
        logger.error(f"Application directory not found: {app_root}")
        return False
    
    # Critical paths that need execute permissions
    critical_paths = [
        app_root / "venv" / "bin",  # All binaries in venv
        app_root / "server.py",
        app_root / "wsgi.py",
        app_root / "deploy_config.py",
    ]
    
    # Add all .py and .sh files in root
    for pattern in ["*.py", "*.sh"]:
        critical_paths.extend(app_root.glob(pattern))
    
    try:
        for path in critical_paths:
            if path.exists():
                if path.is_dir():
                    # For directories like venv/bin, fix all files inside
                    logger.info(f"Fixing directory: {path}")
                    for file_path in path.rglob("*"):
                        if file_path.is_file():
                            # Make executable: 755
                            os.chmod(file_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                            logger.debug(f"  Fixed: {file_path}")
                elif path.is_file():
                    # Make individual file executable: 755
                    logger.info(f"Fixing file: {path}")
                    os.chmod(path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        
        # Also fix the main application directory permissions
        os.chmod(app_root, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
        
        logger.info("Emergency permission fix completed!")
        logger.info("Critical files now have execute permissions restored.")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to fix permissions: {e}")
        return False

def main():
    """Main function"""
    logger = setup_logging()
    
    app_root = sys.argv[1] if len(sys.argv) > 1 else "/opt/nesop-store"
    
    logger.info("NESOP Store Emergency Service Permission Fix")
    logger.info("=" * 50)
    
    if fix_service_permissions(app_root):
        logger.info("\n✓ Emergency fix completed successfully!")
        logger.info("\nNext steps:")
        logger.info("1. Try starting the service:")
        logger.info("   sudo systemctl start nesop-store")
        logger.info("2. Check service status:")
        logger.info("   sudo systemctl status nesop-store")
        logger.info("3. If successful, run the improved fix_permissions.py:")
        logger.info("   sudo python3 fix_permissions.py")
        sys.exit(0)
    else:
        logger.error("Emergency fix failed!")
        sys.exit(1)

if __name__ == "__main__":
    main() 