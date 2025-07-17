#!/usr/bin/env python3
"""
NESOP Store Update Validation
Validates that updates were applied correctly and the system is functioning.
"""

import os
import sys
import json
import subprocess
import requests
import time
from pathlib import Path
from datetime import datetime
import sqlite3
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class UpdateValidator:
    def __init__(self, app_path="/opt/nesop-store"):
        self.app_path = Path(app_path)
        self.service_name = "nesop-store"
        self.base_url = "http://localhost:5000"
        
    def validate_files_exist(self):
        """Validate that essential files exist"""
        logger.info("Validating file existence...")
        
        essential_files = [
            'server.py', 'db_utils.py', 'ad_utils.py', 'config.py',
            'index.html', 'admin.html', 'cart.html', 'register.html',
            'requirements.txt', 'wsgi.py'
        ]
        
        missing_files = []
        for file in essential_files:
            if not (self.app_path / file).exists():
                missing_files.append(file)
        
        if missing_files:
            logger.error(f"Missing essential files: {missing_files}")
            return False
        
        logger.info("✓ All essential files present")
        return True
    
    def validate_service_status(self):
        """Validate that the service is running"""
        logger.info("Validating service status...")
        
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', self.service_name],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                logger.info("✓ Service is active")
                return True
            else:
                logger.error(f"Service is not active: {result.stdout.strip()}")
                return False
                
        except Exception as e:
            logger.error(f"Error checking service status: {e}")
            return False
    
    def validate_database_connection(self):
        """Validate database connectivity"""
        logger.info("Validating database connection...")
        
        try:
            db_path = self.app_path / 'nesop_store_production.db'
            if not db_path.exists():
                logger.error("Database file not found")
                return False
            
            # Test database connection
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()
            
            # Check for required tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['users', 'items', 'carts', 'audit_log']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                logger.error(f"Missing database tables: {missing_tables}")
                conn.close()
                return False
            
            conn.close()
            logger.info("✓ Database connection successful")
            return True
            
        except Exception as e:
            logger.error(f"Database validation failed: {e}")
            return False
    
    def validate_web_response(self):
        """Validate web application response"""
        logger.info("Validating web application response...")
        
        try:
            # Wait for service to be ready
            time.sleep(3)
            
            # Test main page
            response = requests.get(f"{self.base_url}/", timeout=10)
            if response.status_code != 200:
                logger.error(f"Main page returned status {response.status_code}")
                return False
            
            # Test admin page
            response = requests.get(f"{self.base_url}/admin", timeout=10)
            if response.status_code != 200:
                logger.error(f"Admin page returned status {response.status_code}")
                return False
            
            logger.info("✓ Web application responding correctly")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Web application validation failed: {e}")
            return False
    
    def validate_update_history(self):
        """Validate update history log"""
        logger.info("Validating update history...")
        
        try:
            history_file = self.app_path / 'logs' / 'update_history.json'
            if not history_file.exists():
                logger.warning("No update history file found")
                return True
            
            # Read recent updates
            with open(history_file, 'r') as f:
                lines = f.readlines()
                if not lines:
                    logger.info("No update history available")
                    return True
                
                # Parse last update
                last_update = json.loads(lines[-1].strip())
                
                logger.info(f"Last update: {last_update.get('timestamp', 'unknown')}")
                logger.info(f"Update version: {last_update.get('update_version', 'unknown')}")
                logger.info(f"Status: {last_update.get('status', 'unknown')}")
                
                if last_update.get('status') == 'success':
                    logger.info("✓ Last update was successful")
                    return True
                else:
                    logger.warning("Last update status was not successful")
                    return False
                    
        except Exception as e:
            logger.error(f"Error validating update history: {e}")
            return False
    
    def validate_permissions(self):
        """Validate file permissions"""
        logger.info("Validating file permissions...")
        
        try:
            # Check if files are owned by nesop user
            result = subprocess.run(
                ['stat', '-c', '%U', str(self.app_path / 'server.py')],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                owner = result.stdout.strip()
                if owner == 'nesop':
                    logger.info("✓ File permissions correct")
                    return True
                else:
                    logger.warning(f"Files owned by {owner}, expected nesop")
                    return False
            else:
                logger.error("Could not check file permissions")
                return False
                
        except Exception as e:
            logger.error(f"Error checking permissions: {e}")
            return False
    
    def validate_configuration(self):
        """Validate configuration files"""
        logger.info("Validating configuration...")
        
        try:
            # Check for environment file
            env_file = self.app_path / '.env.production'
            if not env_file.exists():
                logger.warning("Production environment file not found")
                return False
            
            # Check for deployment config
            config_file = self.app_path / 'deployment_config.json'
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config = json.load(f)
                    logger.info(f"Configuration loaded: {config.get('app_name', 'unknown')}")
            
            logger.info("✓ Configuration files validated")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False
    
    def run_full_validation(self):
        """Run complete validation suite"""
        logger.info("Starting full update validation...")
        logger.info("=" * 50)
        
        checks = [
            ("File existence", self.validate_files_exist),
            ("Service status", self.validate_service_status),
            ("Database connection", self.validate_database_connection),
            ("Web application", self.validate_web_response),
            ("File permissions", self.validate_permissions),
            ("Configuration", self.validate_configuration),
            ("Update history", self.validate_update_history)
        ]
        
        results = []
        for check_name, check_func in checks:
            logger.info(f"\n--- {check_name} ---")
            try:
                result = check_func()
                results.append((check_name, result))
                if result:
                    logger.info(f"✓ {check_name} passed")
                else:
                    logger.error(f"✗ {check_name} failed")
            except Exception as e:
                logger.error(f"✗ {check_name} error: {e}")
                results.append((check_name, False))
        
        logger.info("\n" + "=" * 50)
        logger.info("VALIDATION SUMMARY")
        logger.info("=" * 50)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for check_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"{status:<8} {check_name}")
        
        logger.info(f"\nResults: {passed}/{total} checks passed")
        
        if passed == total:
            logger.info("🎉 All validation checks passed!")
            logger.info("Update validation completed successfully")
            return True
        else:
            logger.error("❌ Some validation checks failed")
            logger.error("Please review the failures above")
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='NESOP Store Update Validator')
    parser.add_argument('--app-path', default='/opt/nesop-store', help='Application path')
    parser.add_argument('--check', choices=['files', 'service', 'database', 'web', 'permissions', 'config', 'history'], 
                       help='Run specific validation check')
    
    args = parser.parse_args()
    
    validator = UpdateValidator(args.app_path)
    
    if args.check:
        # Run specific check
        check_functions = {
            'files': validator.validate_files_exist,
            'service': validator.validate_service_status,
            'database': validator.validate_database_connection,
            'web': validator.validate_web_response,
            'permissions': validator.validate_permissions,
            'config': validator.validate_configuration,
            'history': validator.validate_update_history
        }
        
        if args.check in check_functions:
            success = check_functions[args.check]()
            sys.exit(0 if success else 1)
        else:
            logger.error(f"Unknown check: {args.check}")
            sys.exit(1)
    else:
        # Run full validation
        success = validator.run_full_validation()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 