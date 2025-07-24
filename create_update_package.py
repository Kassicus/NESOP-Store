#!/usr/bin/env python3
"""
Create NESOP Store Update Package
Generates a lightweight update package for deployed applications.
"""

import os
import sys
import shutil
import tarfile
import json
import hashlib
from pathlib import Path
from datetime import datetime
import argparse

def calculate_file_hash(file_path):
    """Calculate SHA256 hash of a file"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def get_version_from_server():
    """Get version information from server.py"""
    try:
        with open('server.py', 'r') as f:
            content = f.read()
            # Look for version in comments or variables
            if 'version' in content.lower():
                # Extract version if found
                pass
        return "1.0.4"  # Default version
    except:
        return "1.0.4"

def create_update_package(version=None, include_files=None, include_migrations=True):
    """Create a lightweight update package"""
    
    print("Creating NESOP Store Update Package...")
    print("=" * 50)
    
    # Define package name and directory
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if version:
        package_name = f"nesop-store-update-v{version}-{timestamp}"
    else:
        package_name = f"nesop-store-update-{timestamp}"
    
    package_dir = Path(package_name)
    
    # Create package directory
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir()
    
    # Define updateable files (files that commonly change)
    updateable_files = [
        'server.py',
        'db_utils.py',
        'ad_utils.py',
        'config.py',
        'index.html',
        'admin.html',
        'admin-inventory.html',
        'admin-users.html',
        'admin-transactions.html',
        'admin-dashboard.html',
        'cart.html',
        'register.html',
        'account.html'
    ]
    
    # Migration files to include
    migration_files = [
        'migrate_ad_integration.py',
        'migrate_items_to_sqlite.py',
        'migrate_quantity_tracking.py'
    ]
    
    # Utility files
    utility_files = [
        'validate_deployment.py',
        'requirements.txt'
    ]
    
    # Directories to check for updates
    updateable_dirs = [
        'scripts',
        'styles',
        'assets'
    ]
    
    # Files to include in this update
    files_to_include = include_files if include_files else updateable_files
    
    # Create update manifest
    update_manifest = {
        "update_created": datetime.now().isoformat(),
        "update_version": version or "auto",
        "update_type": "rolling_update",
        "target_deployment": "/opt/nesop-store",
        "requires_restart": True,
        "includes_migrations": include_migrations,
        "backup_required": True,
        "files_updated": [],
        "directories_updated": [],
        "migrations_included": [],
        "pre_update_checks": [
            "Verify service is running",
            "Check database connectivity",
            "Verify disk space available"
        ],
        "post_update_checks": [
            "Restart application service",
            "Run database migrations",
            "Validate application startup",
            "Check service health"
        ]
    }
    
    # Copy core application files
    print("Copying application files...")
    for file in files_to_include:
        if Path(file).exists():
            # Calculate hash for change detection
            file_hash = calculate_file_hash(file)
            shutil.copy2(file, package_dir)
            update_manifest["files_updated"].append({
                "file": file,
                "hash": file_hash,
                "size": os.path.getsize(file)
            })
            print(f"  ✓ {file} (hash: {file_hash[:8]}...)")
        else:
            print(f"  ⚠ {file} not found")
    
    # Copy migration files if requested
    if include_migrations:
        print("\nCopying migration files...")
        for file in migration_files:
            if Path(file).exists():
                file_hash = calculate_file_hash(file)
                shutil.copy2(file, package_dir)
                update_manifest["migrations_included"].append({
                    "file": file,
                    "hash": file_hash
                })
                print(f"  ✓ {file}")
        
        # Copy utility files
        for file in utility_files:
            if Path(file).exists():
                shutil.copy2(file, package_dir)
                print(f"  ✓ {file}")
    
    # Copy directories with changes
    print("\nCopying directories...")
    for dir_name in updateable_dirs:
        src_dir = Path(dir_name)
        if src_dir.exists():
            dst_dir = package_dir / dir_name
            shutil.copytree(src_dir, dst_dir)
            update_manifest["directories_updated"].append(dir_name)
            print(f"  ✓ {dir_name}/")
    
    # Create update manifest file
    with open(package_dir / 'update_manifest.json', 'w') as f:
        json.dump(update_manifest, f, indent=2)
    
    print(f"\n✓ Update package created: {package_name}/")
    print(f"✓ Update manifest created: update_manifest.json")
    
    # Create compressed archive
    print(f"\nCreating compressed archive...")
    archive_name = f"{package_name}.tar.gz"
    with tarfile.open(archive_name, 'w:gz') as tar:
        tar.add(package_dir, arcname=package_name)
    
    print(f"✓ Archive created: {archive_name}")
    
    # Calculate sizes
    package_size = sum(f.stat().st_size for f in package_dir.rglob('*') if f.is_file())
    archive_size = Path(archive_name).stat().st_size
    
    print(f"\nUpdate Package Statistics:")
    print(f"  - Package size: {package_size / 1024 / 1024:.2f} MB")
    print(f"  - Archive size: {archive_size / 1024 / 1024:.2f} MB")
    print(f"  - Files included: {len(list(package_dir.rglob('*')))}")
    print(f"  - Files updated: {len(update_manifest['files_updated'])}")
    print(f"  - Directories updated: {len(update_manifest['directories_updated'])}")
    
    print(f"\n" + "=" * 50)
    print("UPDATE PACKAGE READY!")
    print("=" * 50)
    print(f"Package: {package_name}/")
    print(f"Archive: {archive_name}")
    print(f"\nTo apply update:")
    print(f"1. Copy {archive_name} to your server")
    print(f"2. Extract: tar -xzf {archive_name}")
    print(f"3. Run: cd {package_name} && sudo python3 ../nesop-store/update_manager.py apply .")
    print(f"4. Verify: sudo python3 /opt/nesop-store/validate_deployment.py")
    
    return package_name, archive_name

def main():
    parser = argparse.ArgumentParser(description='Create NESOP Store update package')
    parser.add_argument('--version', '-v', help='Version number for the update')
    parser.add_argument('--files', '-f', nargs='+', help='Specific files to include')
    parser.add_argument('--no-migrations', action='store_true', help='Skip migration files')
    
    args = parser.parse_args()
    
    try:
        create_update_package(
            version=args.version,
            include_files=args.files,
            include_migrations=not args.no_migrations
        )
    except Exception as e:
        print(f"Error creating update package: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 