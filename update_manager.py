#!/usr/bin/env python3
"""
NESOP Store Update Manager
Handles applying updates to deployed applications safely.
"""

import os
import sys
import shutil
import subprocess
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
import argparse
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/opt/nesop-store/logs/update.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class UpdateManager:
    def __init__(self, app_path="/opt/nesop-store"):
        self.app_path = Path(app_path)
        self.backup_path = self.app_path / "backups"
        self.service_name = "nesop-store"
        self.backup_path.mkdir(exist_ok=True)
        
    def calculate_file_hash(self, file_path):
        """Calculate SHA256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return None
    
    def create_backup(self, backup_name=None):
        """Create a backup of the current application"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = self.backup_path / backup_name
        logger.info(f"Creating backup: {backup_dir}")
        
        # Files to backup
        files_to_backup = [
            'server.py', 'db_utils.py', 'ad_utils.py', 'config.py',
            'index.html', 'admin.html', 'cart.html', 'register.html',
            'requirements.txt', 'validate_deployment.py'
        ]
        
        # Directories to backup
        dirs_to_backup = ['scripts', 'styles', 'assets']
        
        try:
            backup_dir.mkdir(exist_ok=True)
            
            # Backup files
            for file in files_to_backup:
                src = self.app_path / file
                if src.exists():
                    shutil.copy2(src, backup_dir)
                    logger.debug(f"Backed up: {file}")
            
            # Backup directories
            for dir_name in dirs_to_backup:
                src = self.app_path / dir_name
                if src.exists():
                    dst = backup_dir / dir_name
                    shutil.copytree(src, dst)
                    logger.debug(f"Backed up: {dir_name}/")
            
            # Create backup manifest
            backup_manifest = {
                "created": datetime.now().isoformat(),
                "type": "pre_update_backup",
                "files_backed_up": [f for f in files_to_backup if (self.app_path / f).exists()],
                "directories_backed_up": [d for d in dirs_to_backup if (self.app_path / d).exists()],
                "app_path": str(self.app_path),
                "backup_path": str(backup_dir)
            }
            
            with open(backup_dir / 'backup_manifest.json', 'w') as f:
                json.dump(backup_manifest, f, indent=2)
            
            logger.info(f"✓ Backup created successfully: {backup_name}")
            return backup_name
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None
    
    def check_service_status(self):
        """Check if the service is running"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', self.service_name],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return False
    
    def stop_service(self):
        """Stop the application service"""
        logger.info(f"Stopping service: {self.service_name}")
        try:
            result = subprocess.run(
                ['systemctl', 'stop', self.service_name],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info("✓ Service stopped successfully")
                return True
            else:
                logger.error(f"Failed to stop service: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error stopping service: {e}")
            return False
    
    def start_service(self):
        """Start the application service"""
        logger.info(f"Starting service: {self.service_name}")
        try:
            result = subprocess.run(
                ['systemctl', 'start', self.service_name],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info("✓ Service started successfully")
                return True
            else:
                logger.error(f"Failed to start service: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error starting service: {e}")
            return False
    
    def restart_service(self):
        """Restart the application service"""
        logger.info(f"Restarting service: {self.service_name}")
        try:
            result = subprocess.run(
                ['systemctl', 'restart', self.service_name],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info("✓ Service restarted successfully")
                return True
            else:
                logger.error(f"Failed to restart service: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return False
    
    def run_migrations(self, update_dir):
        """Run database migrations if included in update"""
        logger.info("Running database migrations...")
        
        migration_files = [
            'migrate_ad_integration.py',
            'migrate_items_to_sqlite.py',
            'migrate_username_normalization.py'
        ]
        
        migrations_run = 0
        for migration in migration_files:
            migration_path = update_dir / migration
            if migration_path.exists():
                logger.info(f"Running migration: {migration}")
                try:
                    # Change to app directory and run migration
                    result = subprocess.run(
                        ['python3', str(migration_path)],
                        cwd=str(self.app_path),
                        capture_output=True, text=True
                    )
                    
                    if result.returncode == 0:
                        logger.info(f"✓ Migration completed: {migration}")
                        migrations_run += 1
                    else:
                        logger.error(f"Migration failed: {migration}")
                        logger.error(f"Error output: {result.stderr}")
                        return False
                        
                except Exception as e:
                    logger.error(f"Error running migration {migration}: {e}")
                    return False
        
        if migrations_run > 0:
            logger.info(f"✓ Successfully ran {migrations_run} migrations")
        else:
            logger.info("No migrations to run")
        
        return True
    
    def apply_update(self, update_dir):
        """Apply an update package"""
        update_dir = Path(update_dir)
        
        if not update_dir.exists():
            logger.error(f"Update directory not found: {update_dir}")
            return False
        
        # Load update manifest
        manifest_path = update_dir / 'update_manifest.json'
        if not manifest_path.exists():
            logger.error("Update manifest not found")
            return False
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except Exception as e:
            logger.error(f"Error reading update manifest: {e}")
            return False
        
        logger.info(f"Applying update: {manifest.get('update_version', 'unknown')}")
        logger.info(f"Update type: {manifest.get('update_type', 'unknown')}")
        
        # Pre-update checks
        logger.info("Running pre-update checks...")
        
        # Check if service is running
        if not self.check_service_status():
            logger.warning("Service is not running - this may be expected")
        
        # Check disk space (basic check)
        total, used, free = shutil.disk_usage(self.app_path)
        free_mb = free // (1024 * 1024)
        if free_mb < 100:  # Less than 100MB free
            logger.error(f"Insufficient disk space: {free_mb}MB available")
            return False
        
        # Create backup
        backup_name = f"pre_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if not self.create_backup(backup_name):
            logger.error("Failed to create backup - aborting update")
            return False
        
        # Stop service
        if manifest.get('requires_restart', True):
            if not self.stop_service():
                logger.error("Failed to stop service - aborting update")
                return False
        
        try:
            # Apply file updates
            logger.info("Applying file updates...")
            for file_info in manifest.get('files_updated', []):
                file_name = file_info['file']
                src_path = update_dir / file_name
                dst_path = self.app_path / file_name
                
                if src_path.exists():
                    # Verify hash if provided
                    if 'hash' in file_info:
                        actual_hash = self.calculate_file_hash(src_path)
                        if actual_hash != file_info['hash']:
                            logger.error(f"Hash mismatch for {file_name}")
                            raise Exception(f"Hash verification failed for {file_name}")
                    
                    shutil.copy2(src_path, dst_path)
                    logger.info(f"✓ Updated: {file_name}")
                else:
                    logger.warning(f"File not found in update: {file_name}")
            
            # Apply directory updates
            logger.info("Applying directory updates...")
            for dir_name in manifest.get('directories_updated', []):
                src_path = update_dir / dir_name
                dst_path = self.app_path / dir_name
                
                if src_path.exists():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    logger.info(f"✓ Updated directory: {dir_name}/")
                else:
                    logger.warning(f"Directory not found in update: {dir_name}")
            
            # Run migrations if included
            if manifest.get('includes_migrations', False):
                if not self.run_migrations(update_dir):
                    raise Exception("Migration failed")
            
            # Restart service
            if manifest.get('requires_restart', True):
                if not self.restart_service():
                    raise Exception("Failed to restart service")
            
            # Wait for service to stabilize
            time.sleep(5)
            
            # Verify service is running
            if manifest.get('requires_restart', True):
                if not self.check_service_status():
                    raise Exception("Service failed to start after update")
            
            # Log successful update
            update_log = {
                "timestamp": datetime.now().isoformat(),
                "update_version": manifest.get('update_version', 'unknown'),
                "backup_created": backup_name,
                "files_updated": len(manifest.get('files_updated', [])),
                "directories_updated": len(manifest.get('directories_updated', [])),
                "migrations_run": len(manifest.get('migrations_included', [])),
                "status": "success"
            }
            
            with open(self.app_path / 'logs' / 'update_history.json', 'a') as f:
                f.write(json.dumps(update_log) + '\n')
            
            logger.info("✓ Update applied successfully!")
            logger.info(f"Backup created: {backup_name}")
            logger.info("Run validation to verify the update")
            
            return True
            
        except Exception as e:
            logger.error(f"Update failed: {e}")
            logger.info("Attempting to rollback...")
            
            # Attempt rollback
            if self.rollback(backup_name):
                logger.info("✓ Rollback completed successfully")
            else:
                logger.error("✗ Rollback failed - manual intervention required")
            
            return False
    
    def rollback(self, backup_name):
        """Rollback to a previous backup"""
        backup_dir = self.backup_path / backup_name
        
        if not backup_dir.exists():
            logger.error(f"Backup not found: {backup_name}")
            return False
        
        logger.info(f"Rolling back to backup: {backup_name}")
        
        # Load backup manifest
        manifest_path = backup_dir / 'backup_manifest.json'
        if not manifest_path.exists():
            logger.error("Backup manifest not found")
            return False
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
        except Exception as e:
            logger.error(f"Error reading backup manifest: {e}")
            return False
        
        # Stop service
        self.stop_service()
        
        try:
            # Restore files
            for file_name in manifest.get('files_backed_up', []):
                src_path = backup_dir / file_name
                dst_path = self.app_path / file_name
                
                if src_path.exists():
                    shutil.copy2(src_path, dst_path)
                    logger.info(f"✓ Restored: {file_name}")
            
            # Restore directories
            for dir_name in manifest.get('directories_backed_up', []):
                src_path = backup_dir / dir_name
                dst_path = self.app_path / dir_name
                
                if src_path.exists():
                    if dst_path.exists():
                        shutil.rmtree(dst_path)
                    shutil.copytree(src_path, dst_path)
                    logger.info(f"✓ Restored directory: {dir_name}/")
            
            # Restart service
            if not self.restart_service():
                raise Exception("Failed to restart service after rollback")
            
            # Wait for service to stabilize
            time.sleep(5)
            
            # Verify service is running
            if not self.check_service_status():
                raise Exception("Service failed to start after rollback")
            
            logger.info("✓ Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def list_backups(self):
        """List available backups"""
        backups = []
        
        if not self.backup_path.exists():
            return backups
        
        for backup_dir in self.backup_path.iterdir():
            if backup_dir.is_dir():
                manifest_path = backup_dir / 'backup_manifest.json'
                if manifest_path.exists():
                    try:
                        with open(manifest_path, 'r') as f:
                            manifest = json.load(f)
                        backups.append({
                            'name': backup_dir.name,
                            'created': manifest.get('created', 'unknown'),
                            'type': manifest.get('type', 'unknown'),
                            'files': len(manifest.get('files_backed_up', [])),
                            'directories': len(manifest.get('directories_backed_up', []))
                        })
                    except:
                        pass
        
        return sorted(backups, key=lambda x: x['created'], reverse=True)

def main():
    parser = argparse.ArgumentParser(description='NESOP Store Update Manager')
    parser.add_argument('action', choices=['apply', 'rollback', 'list-backups', 'status'])
    parser.add_argument('target', nargs='?', help='Update directory or backup name')
    parser.add_argument('--app-path', default='/opt/nesop-store', help='Application path')
    
    args = parser.parse_args()
    
    # Check if running as root
    if os.geteuid() != 0:
        print("This script must be run as root (use sudo)")
        sys.exit(1)
    
    manager = UpdateManager(args.app_path)
    
    if args.action == 'apply':
        if not args.target:
            print("Update directory required for apply action")
            sys.exit(1)
        
        success = manager.apply_update(args.target)
        sys.exit(0 if success else 1)
    
    elif args.action == 'rollback':
        if not args.target:
            print("Backup name required for rollback action")
            sys.exit(1)
        
        success = manager.rollback(args.target)
        sys.exit(0 if success else 1)
    
    elif args.action == 'list-backups':
        backups = manager.list_backups()
        if backups:
            print("Available backups:")
            for backup in backups:
                print(f"  {backup['name']} - {backup['created']} ({backup['type']})")
        else:
            print("No backups available")
    
    elif args.action == 'status':
        service_running = manager.check_service_status()
        print(f"Service status: {'Running' if service_running else 'Not running'}")
        print(f"Application path: {manager.app_path}")
        print(f"Backup path: {manager.backup_path}")
        
        backups = manager.list_backups()
        print(f"Available backups: {len(backups)}")

if __name__ == "__main__":
    main() 