#!/usr/bin/env python3
"""
Create NESOP Store Deployment Package
Generates a complete deployment package ready for server transfer.
"""

import os
import sys
import shutil
import tarfile
import json
from pathlib import Path
from datetime import datetime

def create_deployment_package():
    """Create a complete deployment package"""
    
    print("Creating NESOP Store Deployment Package...")
    print("=" * 50)
    
    # Define package name and directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    package_name = f"nesop-store-deployment-{timestamp}"
    package_dir = Path(package_name)
    
    # Create package directory
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Define files to include
    essential_files = [
        'server.py',
        'db_utils.py',
        'ad_utils.py',
        'config.py',
        'migrate_ad_integration.py',
        'deploy_config.py',
        'validate_deployment.py',
        'migrate_items_to_sqlite.py',
        'fix_permissions.py',
        'uninstall_nesop_store.sh',
        'wsgi.py',
        'requirements.txt',
        'index.html',
        'admin.html',
        'cart.html',
        'register.html'
    ]
    
    documentation_files = [
        'README.md',
        'DEPLOYMENT.md',
        'DEPLOYMENT_CHECKLIST.md',
        'AD_CONFIGURATION_TEMPLATE.md',
        'project_goal.md'
    ]
    
    directories_to_copy = [
        'assets',
        'scripts',
        'styles',
        'data'
    ]
    
    # Copy essential files
    print("Copying essential files...")
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, package_dir)
            print(f"  ✓ {file}")
        else:
            print(f"  ⚠ {file} not found")
    
    # Copy documentation
    print("\nCopying documentation...")
    for file in documentation_files:
        if Path(file).exists():
            shutil.copy2(file, package_dir)
            print(f"  ✓ {file}")
        else:
            print(f"  ⚠ {file} not found")
    
    # Copy directories
    print("\nCopying directories...")
    for dir_name in directories_to_copy:
        src_dir = Path(dir_name)
        if src_dir.exists():
            dst_dir = package_dir / dir_name
            shutil.copytree(src_dir, dst_dir)
            print(f"  ✓ {dir_name}/")
        else:
            print(f"  ⚠ {dir_name}/ not found")
    
    # Create necessary empty directories
    print("\nCreating directory structure...")
    required_dirs = ['logs', 'backups', 'static']
    for dir_name in required_dirs:
        (package_dir / dir_name).mkdir(exist_ok=True)
        print(f"  ✓ {dir_name}/")
    
    # Create empty .gitkeep files in empty directories
    for dir_name in required_dirs:
        (package_dir / dir_name / '.gitkeep').touch()
    
    # Create deployment info file
    deployment_info = {
        "package_created": datetime.now().isoformat(),
        "package_version": "1.0.4",
        "python_version_required": "3.8+",
        "system_requirements": "Ubuntu 20.04 LTS or newer",
        "deployment_type": "internal_server",
        "ad_integration": "enabled",
        "recent_fixes": [
            "Fixed database path synchronization in migrations",
            "Added table existence checking in migration script", 
            "Improved deployment database initialization",
            "Enhanced error handling for fresh deployments",
            "Fixed database schema mismatch for items table",
            "Updated AD configuration to use insecure LDAP (port 389)",
            "Fixed DN pattern duplication bug in AD authentication",
            "Hidden AD user search panel when using simple bind mode",
            "Fixed username display to show clean username instead of email address"
        ],
        "features": [
            "Active Directory integration with simple bind mode",
            "Mock AD for testing and development",
            "User management with local admin permissions",
            "Admin panel with user import/management",
            "Store frontend with shopping cart",
            "Audit logging for security",
            "Automatic deployment with configuration wizard",
            "Database validation and migration tools"
        ],
        "included_tools": [
            "deploy_config.py - Interactive deployment configuration",
            "validate_deployment.py - Deployment validation and testing",
            "migrate_ad_integration.py - AD integration database migration",
            "migrate_items_to_sqlite.py - Item data migration utility",
            "uninstall_nesop_store.sh - Complete application uninstall script"
        ],
        "deployment_steps": [
            "1. Copy package to server",
            "2. Run: python3 deploy_config.py (interactive setup)",
            "3. Run: sudo ./deploy.sh",
            "4. Configure AD settings if needed",
            "5. Test with validate_deployment.py",
            "6. Change default admin password"
        ]
    }
    
    with open(package_dir / 'deployment_info.json', 'w') as f:
        json.dump(deployment_info, f, indent=2)
    
    # Create quick start guide
    quick_start = f"""# NESOP Store - Quick Start Guide

## Package Information
- Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- Version: 1.0.4
- Type: Internal Server Deployment with AD Integration

## What's Included
- Complete application code
- Database migration scripts
- AD integration with mock testing
- Automated deployment scripts
- Nginx and systemd configuration
- Comprehensive documentation

## Quick Deployment (3 Steps)

### Step 1: Copy to Server
```bash
# Copy this entire folder to your server
scp -r {package_name}/ user@your-server:/tmp/
ssh user@your-server
cd /tmp/{package_name}
```

### Step 2: Configure
```bash
# Run interactive configuration
python3 deploy_config.py

# Follow the prompts for:
# - Server settings (host, port, workers)
# - AD configuration (server, domain, service account)
# - Application settings (store name, currency)
```

### Step 3: Deploy
```bash
# Run automated deployment
chmod +x deploy.sh
sudo ./deploy.sh
```

## After Deployment

### Test Access
- URL: http://your-server-ip/
- Default admin: fallback_admin / ChangeMe123!
- Change default password immediately!

### Configure AD
1. Follow AD_CONFIGURATION_TEMPLATE.md
2. Update .env.production with your AD settings
3. Restart service: sudo systemctl restart nesop-store

### Verify
- Run validation: `python3 validate_deployment.py`
- Test AD user login
- Test admin panel access
- Test AD user search/import
- Verify all functionality works

## Files Overview
- `server.py` - Main Flask application
- `deploy_config.py` - Deployment configuration wizard
- `validate_deployment.py` - Deployment validation and testing
- `migrate_ad_integration.py` - AD integration database migration
- `migrate_items_to_sqlite.py` - Item data migration utility
- `uninstall_nesop_store.sh` - Complete application uninstall script
- `AD_CONFIGURATION_TEMPLATE.md` - AD setup guide
- `DEPLOYMENT.md` - Complete deployment guide
- `DEPLOYMENT_CHECKLIST.md` - Deployment checklist
- `wsgi.py` - Production WSGI configuration
- `requirements.txt` - Python dependencies

## Support
- Read DEPLOYMENT.md for detailed instructions
- Check DEPLOYMENT_CHECKLIST.md for verification steps
- Follow AD_CONFIGURATION_TEMPLATE.md for AD setup
- Check logs in /opt/nesop-store/logs/

## Uninstall/Redeploy
If you need to completely remove the application:
```bash
# Run the uninstall script
chmod +x uninstall_nesop_store.sh
sudo ./uninstall_nesop_store.sh
```

This will:
- Stop and remove the systemd service
- Remove all application files and directories
- Clean up nginx configuration
- Remove database files and backups
- Clean up logs and temporary files
- Optionally remove the system user
- Provide verification of cleanup

## Recent Improvements (v1.0.4)
- Fixed database path synchronization in migration scripts
- Added table existence checking for robust deployment
- Enhanced error handling for fresh deployments
- Improved deployment validation and testing tools
- Added comprehensive uninstall script for clean redeployment
- Fixed database schema mismatch for items table
- Updated AD configuration to use insecure LDAP (port 389)
- Fixed DN pattern duplication bug in AD authentication
- Hidden AD user search panel when using simple bind mode
- Fixed username display to show clean username instead of email address

## Security Notes
- Deploy on internal network only
- Use LDAPS for AD connections
- Change default passwords immediately
- Regular security updates
- Run validation after deployment

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open(package_dir / 'QUICK_START.md', 'w') as f:
        f.write(quick_start)
    
    print(f"\n✓ Deployment package created: {package_name}/")
    print("\nPackage contents:")
    print(f"  - Essential application files")
    print(f"  - Complete documentation")
    print(f"  - Deployment scripts")
    print(f"  - Configuration tools")
    print(f"  - Assets and frontend files")
    
    # Create compressed archive
    print(f"\nCreating compressed archive...")
    archive_name = f"{package_name}.tar.gz"
    with tarfile.open(archive_name, 'w:gz') as tar:
        tar.add(package_dir, arcname=package_name)
    
    print(f"✓ Archive created: {archive_name}")
    
    # Calculate sizes
    package_size = sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file())
    archive_size = Path(archive_name).stat().st_size
    
    print(f"\nPackage Statistics:")
    print(f"  - Package size: {package_size / 1024 / 1024:.2f} MB")
    print(f"  - Archive size: {archive_size / 1024 / 1024:.2f} MB")
    print(f"  - Files included: {len(list(package_dir.rglob('*')))}")
    
    print(f"\n" + "=" * 50)
    print("DEPLOYMENT PACKAGE READY!")
    print("=" * 50)
    print(f"Package: {package_name}/")
    print(f"Archive: {archive_name}")
    print(f"\nTo deploy:")
    print(f"1. Copy {archive_name} to your server")
    print(f"2. Extract: tar -xzf {archive_name}")
    print(f"3. Run: cd {package_name} && python3 deploy_config.py")
    print(f"4. Deploy: sudo ./deploy.sh")
    print(f"5. Configure AD settings")
    print(f"6. Test and verify")
    
    return package_name, archive_name

if __name__ == "__main__":
    try:
        create_deployment_package()
    except Exception as e:
        print(f"Error creating deployment package: {e}")
        sys.exit(1) 