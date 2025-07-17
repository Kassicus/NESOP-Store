#!/usr/bin/env python3
"""
NESOP Store Deployment Validation Script
Validates the deployment configuration and tests all components.
"""

import os
import sys
import sqlite3
import json
from pathlib import Path
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DeploymentValidator:
    """Validates deployment configuration and components"""
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.passed = []
        
    def log_error(self, message):
        """Log an error"""
        self.errors.append(message)
        logger.error(message)
    
    def log_warning(self, message):
        """Log a warning"""
        self.warnings.append(message)
        logger.warning(message)
    
    def log_passed(self, message):
        """Log a passed test"""
        self.passed.append(message)
        logger.info(f"✓ {message}")
    
    def validate_files(self):
        """Validate required files exist"""
        print("1. Validating Required Files...")
        print("-" * 40)
        
        required_files = [
            'server.py',
            'db_utils.py',
            'ad_utils.py',
            'config.py',
            'migrate_ad_integration.py',
            'deploy_config.py',
            'wsgi.py',
            'requirements.txt'
        ]
        
        for file in required_files:
            if Path(file).exists():
                self.log_passed(f"Required file exists: {file}")
            else:
                self.log_error(f"Missing required file: {file}")
        
        # Check HTML files
        html_files = ['index.html', 'admin.html', 'cart.html', 'register.html']
        for file in html_files:
            if Path(file).exists():
                self.log_passed(f"HTML file exists: {file}")
            else:
                self.log_warning(f"HTML file missing: {file}")
        
        # Check directories
        directories = ['assets', 'scripts', 'styles']
        for dir_name in directories:
            if Path(dir_name).exists():
                self.log_passed(f"Directory exists: {dir_name}")
            else:
                self.log_warning(f"Directory missing: {dir_name}")
    
    def validate_python_imports(self):
        """Validate Python imports work correctly"""
        print("\n2. Validating Python Imports...")
        print("-" * 40)
        
        modules_to_test = [
            ('db_utils', 'Database utilities'),
            ('ad_utils', 'AD utilities'),
            ('config', 'Configuration management'),
            ('migrate_ad_integration', 'Database migration'),
            ('deploy_config', 'Deployment configuration'),
            ('server', 'Flask server')
        ]
        
        for module_name, description in modules_to_test:
            try:
                __import__(module_name)
                self.log_passed(f"Import successful: {module_name} ({description})")
            except ImportError as e:
                self.log_error(f"Import failed: {module_name} - {str(e)}")
            except Exception as e:
                self.log_warning(f"Import issue: {module_name} - {str(e)}")
    
    def validate_database_setup(self):
        """Validate database setup and migration"""
        print("\n3. Validating Database Setup...")
        print("-" * 40)
        
        try:
            # Test database creation
            test_db = 'test_validation.db'
            if Path(test_db).exists():
                os.remove(test_db)
            
            # Import and test database utilities
            import db_utils
            original_path = db_utils.DB_PATH
            db_utils.DB_PATH = test_db
            
            # Test database connection
            conn = sqlite3.connect(test_db)
            conn.close()
            self.log_passed("Database connection test successful")
            
                         # Create base database structure first
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            
            # Create basic tables that the migration expects
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                balance INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                price REAL NOT NULL,
                image TEXT,
                description TEXT
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                item_id INTEGER NOT NULL,
                rating INTEGER NOT NULL,
                comment TEXT,
                review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            conn.commit()
            conn.close()
            
            # Test migration
            import migrate_ad_integration
            migrate_ad_integration.main()
            self.log_passed("Database migration successful")
            
                         # Test database functions
            conn = sqlite3.connect(test_db)
            cursor = conn.cursor()
            
            # Check tables exist
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['users', 'items', 'purchases', 'reviews', 'ad_config', 'ad_audit_log']
            for table in expected_tables:
                if table in tables:
                    self.log_passed(f"Database table exists: {table}")
                else:
                    self.log_error(f"Database table missing: {table}")
            
            # Test user creation (check if fallback admin exists)
            try:
                cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'fallback_admin'")
                if cursor.fetchone()[0] > 0:
                    self.log_passed("Fallback admin user exists")
                else:
                    self.log_error("Fallback admin user missing")
            except sqlite3.Error as e:
                self.log_error(f"Error checking fallback admin: {e}")
            
            conn.close()
            
            # Cleanup
            os.remove(test_db)
            db_utils.DB_PATH = original_path
            
        except Exception as e:
            self.log_error(f"Database setup validation failed: {str(e)}")
    
    def validate_ad_configuration(self):
        """Validate AD configuration and mock system"""
        print("\n4. Validating AD Configuration...")
        print("-" * 40)
        
        try:
            # Test config system
            import config
            app_config = config.get_config()
            self.log_passed("Configuration system working")
            
            # Test AD utilities
            import ad_utils
            
            # Test with mock AD
            os.environ['AD_ENABLED'] = 'true'
            os.environ['USE_MOCK_AD'] = 'true'
            
            ad_manager = ad_utils.ActiveDirectoryManager()
            self.log_passed("AD Manager initialization successful")
            
            # Test mock authentication
            result = ad_manager.authenticate_user('jsmith', 'password123')
            if result[0]:
                self.log_passed("Mock AD authentication working")
            else:
                self.log_error("Mock AD authentication failed")
            
            # Test user search
            users = ad_manager.search_users('*', 10)
            if len(users) > 0:
                self.log_passed(f"Mock AD user search working ({len(users)} users)")
            else:
                self.log_error("Mock AD user search failed")
            
            # Test admin detection
            admin_status = ad_manager.is_user_admin(users[0]) if users else False
            self.log_passed(f"Mock AD admin detection working")
            
        except Exception as e:
            self.log_error(f"AD configuration validation failed: {str(e)}")
    
    def validate_deployment_configuration(self):
        """Validate deployment configuration system"""
        print("\n5. Validating Deployment Configuration...")
        print("-" * 40)
        
        try:
            from deploy_config import DeploymentConfig
            
            deploy_config = DeploymentConfig()
            self.log_passed("Deployment configuration system working")
            
            # Test config loading
            config = deploy_config.load_config()
            self.log_passed("Default configuration loaded")
            
            # Test secret key generation
            secret = deploy_config.generate_secret_key()
            if len(secret) > 20:
                self.log_passed("Secret key generation working")
            else:
                self.log_error("Secret key generation failed")
            
            # Test configuration validation
            required_sections = ['deployment', 'database', 'security', 'ad_integration', 'app_settings']
            for section in required_sections:
                if section in config:
                    self.log_passed(f"Configuration section exists: {section}")
                else:
                    self.log_error(f"Configuration section missing: {section}")
            
        except Exception as e:
            self.log_error(f"Deployment configuration validation failed: {str(e)}")
    
    def validate_wsgi_configuration(self):
        """Validate WSGI configuration"""
        print("\n6. Validating WSGI Configuration...")
        print("-" * 40)
        
        try:
            # Test WSGI import
            import wsgi
            self.log_passed("WSGI module import successful")
            
            # Test Flask app
            if hasattr(wsgi, 'application'):
                self.log_passed("WSGI application object exists")
            else:
                self.log_error("WSGI application object missing")
            
            # Test Flask app configuration
            app = wsgi.application
            if hasattr(app, 'config'):
                self.log_passed("Flask app configuration accessible")
            else:
                self.log_error("Flask app configuration missing")
            
        except Exception as e:
            self.log_error(f"WSGI configuration validation failed: {str(e)}")
    
    def validate_requirements(self):
        """Validate requirements.txt"""
        print("\n7. Validating Requirements...")
        print("-" * 40)
        
        try:
            with open('requirements.txt', 'r') as f:
                requirements = f.read().strip().split('\n')
            
            expected_packages = ['Flask', 'ldap3', 'gunicorn', 'supervisor']
            
            for package in expected_packages:
                found = any(package in req for req in requirements)
                if found:
                    self.log_passed(f"Required package listed: {package}")
                else:
                    self.log_error(f"Required package missing: {package}")
            
            self.log_passed(f"Total packages in requirements: {len(requirements)}")
            
        except Exception as e:
            self.log_error(f"Requirements validation failed: {str(e)}")
    
    def validate_mock_ad_functionality(self):
        """Validate mock AD functionality for testing"""
        print("\n8. Validating Mock AD Functionality...")
        print("-" * 40)
        
        try:
            # Set environment for mock AD
            os.environ['AD_ENABLED'] = 'true'
            os.environ['USE_MOCK_AD'] = 'true'
            
            import ad_utils
            ad_manager = ad_utils.ActiveDirectoryManager()
            
            # Test all mock users
            mock_users = ['jsmith', 'mjohnson', 'bwilson', 'admin']
            for username in mock_users:
                result = ad_manager.authenticate_user(username, 'password123')
                if result[0]:
                    self.log_passed(f"Mock user authentication: {username}")
                else:
                    self.log_error(f"Mock user authentication failed: {username}")
            
            # Test user search
            all_users = ad_manager.search_users('*', 10)
            if len(all_users) == 4:
                self.log_passed("All mock users found in search")
            else:
                self.log_warning(f"Expected 4 mock users, found {len(all_users)}")
            
            # Test admin detection
            admin_users = [u for u in all_users if ad_manager.is_user_admin(u)]
            if len(admin_users) > 0:
                self.log_passed(f"Mock admin detection working ({len(admin_users)} admins)")
            else:
                self.log_error("Mock admin detection failed")
                
        except Exception as e:
            self.log_error(f"Mock AD functionality validation failed: {str(e)}")
    
    def generate_report(self):
        """Generate validation report"""
        print("\n" + "=" * 60)
        print("DEPLOYMENT VALIDATION REPORT")
        print("=" * 60)
        
        print(f"\n✓ PASSED: {len(self.passed)} tests")
        print(f"⚠ WARNINGS: {len(self.warnings)} issues")
        print(f"✗ ERRORS: {len(self.errors)} critical issues")
        
        if self.errors:
            print("\nCRITICAL ERRORS (Must Fix):")
            for error in self.errors:
                print(f"  ✗ {error}")
        
        if self.warnings:
            print("\nWARNINGS (Should Fix):")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        print("\nSUMMARY:")
        if len(self.errors) == 0:
            print("✓ DEPLOYMENT READY - All critical tests passed!")
            print("  You can proceed with deployment to your server.")
            if self.warnings:
                print("  Note: Some warnings exist but won't prevent deployment.")
        else:
            print("✗ DEPLOYMENT NOT READY - Critical errors found!")
            print("  Please fix the errors above before deploying.")
        
        print("\nNEXT STEPS:")
        if len(self.errors) == 0:
            print("1. Run: python3 create_deployment_package.py")
            print("2. Copy package to your server")
            print("3. Follow AD_CONFIGURATION_TEMPLATE.md")
            print("4. Run deployment on server")
        else:
            print("1. Fix the critical errors listed above")
            print("2. Run this validation script again")
            print("3. Once all errors are fixed, create deployment package")
        
        print("=" * 60)
        
        return len(self.errors) == 0

def main():
    """Main validation function"""
    print("NESOP Store Deployment Validation")
    print("=" * 60)
    print("This script validates your deployment configuration")
    print("before creating the deployment package.\n")
    
    validator = DeploymentValidator()
    
    # Run all validation tests
    validator.validate_files()
    validator.validate_python_imports()
    validator.validate_database_setup()
    validator.validate_ad_configuration()
    validator.validate_deployment_configuration()
    validator.validate_wsgi_configuration()
    validator.validate_requirements()
    validator.validate_mock_ad_functionality()
    
    # Generate report
    success = validator.generate_report()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main()) 