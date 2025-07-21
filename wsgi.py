#!/usr/bin/env python3
"""
WSGI Entry Point for NESOP Store
Production-ready WSGI configuration for deployment.
"""

import os
import sys
import logging
from pathlib import Path

# Add the application directory to the Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables from .env.production if it exists
def load_env_file(file_path):
    """Load environment variables from a file"""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# Load production environment if available
load_env_file('.env.production')

# Configure logging for production
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
log_file = os.getenv('LOG_FILE', 'nesop_store.log')
log_max_size = int(os.getenv('LOG_MAX_SIZE', '10485760'))  # 10MB
log_backup_count = int(os.getenv('LOG_BACKUP_COUNT', '5'))

from logging.handlers import RotatingFileHandler

# Setup production logging
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure root logger
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            f'logs/{log_file}',
            maxBytes=log_max_size,
            backupCount=log_backup_count
        ),
        logging.StreamHandler()
    ]
)

# Import and configure the Flask application
try:
    from server import app
    
    # Set production configuration
    app.config['DEBUG'] = False
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-this-in-production')
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_FILE_SIZE', '16777216'))  # 16MB
    
    # Configure database path for production
    database_path = os.getenv('DATABASE_PATH', 'nesop_store_production.db')
    if not os.path.isabs(database_path):
        database_path = os.path.join(os.path.dirname(__file__), database_path)
    
    # Update database configuration
    import db_utils
    db_utils.DB_PATH = database_path
    
    # Configure upload folder
    upload_path = os.getenv('UPLOAD_PATH', 'assets/images')
    if not os.path.isabs(upload_path):
        upload_path = os.path.join(os.path.dirname(__file__), upload_path)
    
    app.config['UPLOAD_FOLDER'] = upload_path
    
    # Ensure upload directory exists with proper permissions
    os.makedirs(upload_path, exist_ok=True)
    
    # Log startup information
    logger = logging.getLogger(__name__)
    
    # Set proper permissions for upload directory (readable and writable by group)
    try:
        import stat
        import grp
        import pwd
        
        # Set directory permissions to 775 (owner: rwx, group: rwx, others: r-x)
        os.chmod(upload_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IROTH | stat.S_IXOTH)
        
        # Try to set group ownership to www-data if it exists
        try:
            www_data_gid = grp.getgrnam('www-data').gr_gid
            os.chown(upload_path, -1, www_data_gid)  # -1 means don't change owner, only group
            logger.info(f"Set upload directory group to www-data: {upload_path}")
        except (KeyError, OSError) as e:
            # If www-data group doesn't exist, try to make it writable by all
            os.chmod(upload_path, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)
            logger.warning(f"Could not set www-data group ownership, made directory world-writable: {e}")
            
    except Exception as e:
        logger.error(f"Could not set upload directory permissions: {e}")
        logger.warning("Upload functionality may not work without proper permissions")
    logger.info("NESOP Store application starting...")
    logger.info(f"Database path: {database_path}")
    logger.info(f"Upload folder: {upload_path}")
    logger.info(f"Debug mode: {app.config.get('DEBUG', False)}")
    logger.info(f"AD Integration: {os.getenv('AD_ENABLED', 'false')}")
    logger.info(f"Mock AD: {os.getenv('AD_USE_MOCK', 'false')}")
    
    # Test database connection
    try:
        import sqlite3
        conn = sqlite3.connect(database_path)
        conn.close()
        logger.info("Database connection test successful")
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
    
    # Test AD configuration if enabled
    if os.getenv('AD_ENABLED', 'false').lower() == 'true':
        try:
            import ad_utils
            ad_manager = ad_utils.ActiveDirectoryManager()
            logger.info("AD manager initialized successfully")
        except Exception as e:
            logger.error(f"AD manager initialization failed: {e}")
    
    logger.info("NESOP Store application initialized successfully")
    
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to initialize application: {e}")
    raise

# Export the application for WSGI
application = app

if __name__ == "__main__":
    # This allows running the application directly for testing
    port = int(os.getenv('DEPLOYMENT_PORT', '8080'))
    host = os.getenv('DEPLOYMENT_HOST', '0.0.0.0')
    debug = os.getenv('DEBUG', 'false').lower() == 'true'
    
    app.run(host=host, port=port, debug=debug)