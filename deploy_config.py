#!/usr/bin/env python3
"""
NESOP Store - Deployment Configuration Script
Handles production setup and environment configuration for internal server deployment.
"""

import os
import sys
import sqlite3
import secrets
import logging
from pathlib import Path
from datetime import datetime
import subprocess
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('deployment.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DeploymentConfig:
    """Handles deployment configuration and setup"""
    
    def __init__(self, config_file='deployment_config.json'):
        self.config_file = config_file
        self.app_root = Path(__file__).parent
        self.default_config = {
            'deployment': {
                'environment': 'production',
                'host': '0.0.0.0',
                'port': 8080,
                'debug': False,
                'workers': 4,
                'timeout': 120
            },
            'database': {
                'path': 'nesop_store_production.db',
                'backup_enabled': True,
                'backup_retention_days': 30
            },
            'security': {
                'secret_key': '',
                'session_timeout': 3600,
                'max_login_attempts': 5,
                'lockout_duration': 900
            },
            'logging': {
                'level': 'INFO',
                'file': 'nesop_store.log',
                'max_size': 10485760,  # 10MB
                'backup_count': 5
            },
            'ad_integration': {
                'enabled': True,
                'use_mock': False,
                'simple_bind_mode': True,
                'server_url': 'ldap://your-dc.yourdomain.com',
                'domain': 'yourdomain.com',
                'bind_dn': 'CN=service_account,OU=Service Accounts,DC=yourdomain,DC=com',
                'bind_password': '',
                'user_base_dn': 'OU=Users,DC=yourdomain,DC=com',
                'user_dn_pattern': '{username}@{domain}',
                'admin_group': '',  # Optional: Leave empty to manage admin permissions locally
                'use_ssl': False,
                'port': 389,
                'timeout': 10
            },
            'app_settings': {
                'store_name': 'NESOP Store',
                'currency_symbol': '₦',
                'max_file_size': 16777216,  # 16MB
                'allowed_extensions': ['.jpg', '.jpeg', '.png', '.gif', '.webp'],
                'upload_path': 'assets/images',
                'session_lifetime': 86400  # 24 hours
            }
        }
        
    def load_config(self):
        """Load configuration from file or create default"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                logger.info(f"Loaded configuration from {self.config_file}")
                return config
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                return self.default_config
        else:
            logger.info("No configuration file found, using defaults")
            return self.default_config.copy()
    
    def save_config(self, config):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"Configuration saved to {self.config_file}")
        except Exception as e:
            logger.error(f"Error saving config file: {e}")
    
    def generate_secret_key(self):
        """Generate a secure secret key"""
        return secrets.token_urlsafe(32)
    
    def create_production_env(self, config):
        """Create production environment file"""
        env_content = f"""# NESOP Store Production Environment Configuration
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

# Flask Configuration
FLASK_ENV=production
SECRET_KEY={config['security']['secret_key']}
DEBUG=false

# Database Configuration
DATABASE_PATH={config['database']['path']}

# AD Integration
AD_ENABLED={str(config['ad_integration']['enabled']).lower()}
AD_USE_MOCK={str(config['ad_integration']['use_mock']).lower()}
AD_SIMPLE_BIND_MODE={str(config['ad_integration']['simple_bind_mode']).lower()}
AD_SERVER_URL={config['ad_integration']['server_url']}
AD_DOMAIN={config['ad_integration']['domain']}
AD_BIND_DN={config['ad_integration']['bind_dn']}
AD_BIND_PASSWORD={config['ad_integration']['bind_password']}
AD_USER_BASE_DN={config['ad_integration']['user_base_dn']}
AD_USER_DN_PATTERN={config['ad_integration']['user_dn_pattern']}
AD_ADMIN_GROUP={config['ad_integration']['admin_group']}
AD_USE_SSL={str(config['ad_integration']['use_ssl']).lower()}
AD_PORT={config['ad_integration']['port']}
AD_TIMEOUT={config['ad_integration']['timeout']}

# Application Settings
STORE_NAME={config['app_settings']['store_name']}
CURRENCY_SYMBOL={config['app_settings']['currency_symbol']}
MAX_FILE_SIZE={config['app_settings']['max_file_size']}
UPLOAD_PATH={config['app_settings']['upload_path']}
SESSION_LIFETIME={config['app_settings']['session_lifetime']}

# Logging
LOG_LEVEL={config['logging']['level']}
LOG_FILE={config['logging']['file']}
LOG_MAX_SIZE={config['logging']['max_size']}
LOG_BACKUP_COUNT={config['logging']['backup_count']}

# Security
SESSION_TIMEOUT={config['security']['session_timeout']}
MAX_LOGIN_ATTEMPTS={config['security']['max_login_attempts']}
LOCKOUT_DURATION={config['security']['lockout_duration']}

# Deployment
DEPLOYMENT_HOST={config['deployment']['host']}
DEPLOYMENT_PORT={config['deployment']['port']}
DEPLOYMENT_WORKERS={config['deployment']['workers']}
DEPLOYMENT_TIMEOUT={config['deployment']['timeout']}
"""
        
        with open('.env.production', 'w') as f:
            f.write(env_content)
        logger.info("Production environment file created: .env.production")
    
    def create_base_tables(self, db_path):
        """Create base database tables before running migrations"""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create users table
            cursor.execute('''CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL,
                balance INTEGER DEFAULT 0,
                is_admin INTEGER DEFAULT 0,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Create items table (schema must match what db_utils.py expects)
            cursor.execute('''CREATE TABLE IF NOT EXISTS items (
                item TEXT PRIMARY KEY,
                description TEXT,
                price REAL,
                image TEXT,
                sold_out INTEGER DEFAULT 0,
                unlisted INTEGER DEFAULT 0,
                quantity INTEGER DEFAULT 0
            )''')
            
            # Create purchases table
            cursor.execute('''CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                item TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                total_price REAL NOT NULL,
                purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (username) REFERENCES users(username),
                FOREIGN KEY (item) REFERENCES items(item)
            )''')
            
            # Create reviews table
            cursor.execute('''CREATE TABLE IF NOT EXISTS reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                item TEXT NOT NULL,
                username TEXT,
                rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                review_text TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
            
            # Create fallback admin user
            cursor.execute('''INSERT OR IGNORE INTO users (username, password, balance, is_admin) 
                              VALUES ('fallback_admin', 'ChangeMe123!', 1000, 1)''')
            
            conn.commit()
            conn.close()
            logger.info("Base database tables created successfully")
            
        except Exception as e:
            logger.error(f"Error creating base tables: {str(e)}")
            raise

    def setup_database(self, config):
        """Setup production database"""
        db_path = config['database']['path']
        
        if os.path.exists(db_path):
            logger.info(f"Database already exists: {db_path}")
            backup_path = f"{db_path}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            os.system(f"cp {db_path} {backup_path}")
            logger.info(f"Database backup created: {backup_path}")
        else:
            logger.info(f"Creating new production database: {db_path}")
            
            # Import and run database setup
            import db_utils
            import migrate_ad_integration
            
            # Set database path for production
            db_utils.DB_PATH = db_path
            
            # Create base database tables first
            self.create_base_tables(db_path)
            
            # Run migration to add AD integration columns
            migrate_ad_integration.main()
            logger.info("Production database initialized successfully")
    
    def setup_directories(self, config):
        """Create necessary directories"""
        directories = [
            config['app_settings']['upload_path'],
            'logs',
            'backups',
            'static',
            'data'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
    
    def setup_systemd_service(self, config):
        """Create systemd service file"""
        # Use the final deployment path, not the current working directory
        app_root = "/opt/nesop-store"
        service_content = f"""[Unit]
Description=NESOP Store Application
After=network.target
Wants=network.target

[Service]
Type=notify
User=nesop
Group=nesop
WorkingDirectory={app_root}
Environment=PATH={app_root}/venv/bin
ExecStart={app_root}/venv/bin/gunicorn --bind {config['deployment']['host']}:{config['deployment']['port']} --workers {config['deployment']['workers']} --timeout {config['deployment']['timeout']} --access-logfile logs/access.log --error-logfile logs/error.log wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
RestartSec=10
Restart=always

[Install]
WantedBy=multi-user.target
"""
        
        with open('nesop-store.service', 'w') as f:
            f.write(service_content)
        logger.info("Systemd service file created: nesop-store.service")
    
    def setup_nginx_config(self, config):
        """Create nginx configuration"""
        # Use the final deployment path, not the current working directory
        app_root = "/opt/nesop-store"
        nginx_content = f"""server {{
    listen 80;
    server_name your-internal-server.yourdomain.com;
    
    # Optional: Redirect to HTTPS
    # return 301 https://$server_name$request_uri;
    
    location / {{
        proxy_pass http://127.0.0.1:{config['deployment']['port']};
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Increase timeout for AD operations
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }}
    
    location /assets/ {{
        alias {app_root}/assets/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
    
    location /static/ {{
        alias {app_root}/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # File upload size limit
    client_max_body_size 20M;
    
    # Logging
    access_log /var/log/nginx/nesop-store.access.log;
    error_log /var/log/nginx/nesop-store.error.log;
}}

# Optional HTTPS configuration
# server {{
#     listen 443 ssl http2;
#     server_name your-internal-server.yourdomain.com;
#     
#     ssl_certificate /path/to/your/certificate.pem;
#     ssl_certificate_key /path/to/your/private.key;
#     
#     # Same location blocks as above
# }}
"""
        
        with open('nesop-store.nginx', 'w') as f:
            f.write(nginx_content)
        logger.info("Nginx configuration created: nesop-store.nginx")
    
    def create_deployment_script(self, config):
        """Create deployment script"""
        script_content = f"""#!/bin/bash
# NESOP Store Deployment Script
# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

set -e

echo "Starting NESOP Store deployment..."

# Create application user
if ! id "nesop" &>/dev/null; then
    sudo useradd -r -s /bin/false nesop
    echo "Created nesop user"
fi

# Create directories
sudo mkdir -p /opt/nesop-store
sudo chown nesop:nesop /opt/nesop-store

# Copy application files
sudo cp -r . /opt/nesop-store/
sudo chown -R nesop:nesop /opt/nesop-store/

# Install system dependencies
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y python3 python3-pip python3-venv nginx supervisor

# Create virtual environment
cd /opt/nesop-store
sudo -u nesop python3 -m venv venv
sudo -u nesop venv/bin/pip install -r requirements.txt

# Setup database
echo "Setting up database..."
sudo -u nesop venv/bin/python3 deploy_config.py --setup-db

# Copy service files
sudo cp nesop-store.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nesop-store

# Setup nginx
sudo cp nesop-store.nginx /etc/nginx/sites-available/nesop-store
sudo ln -sf /etc/nginx/sites-available/nesop-store /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Start services
sudo systemctl start nesop-store
sudo systemctl status nesop-store

echo "Deployment completed successfully!"
echo "Application should be accessible at: http://your-server-ip/"
echo "Default admin credentials: fallback_admin / ChangeMe123!"
echo "Please change the default password after first login."
"""
        
        with open('deploy.sh', 'w') as f:
            f.write(script_content)
        os.chmod('deploy.sh', 0o755)
        logger.info("Deployment script created: deploy.sh")
    
    def interactive_setup(self):
        """Interactive setup for deployment configuration"""
        print("\n" + "="*60)
        print("NESOP Store - Deployment Configuration Setup")
        print("="*60)
        
        config = self.load_config()
        
        # Generate secret key if not exists
        if not config['security']['secret_key']:
            config['security']['secret_key'] = self.generate_secret_key()
            print("✓ Generated new secret key")
        
        # Basic deployment settings
        print("\n1. Basic Deployment Settings")
        print("-" * 30)
        
        host = input(f"Server host [{config['deployment']['host']}]: ").strip()
        if host:
            config['deployment']['host'] = host
        
        port = input(f"Server port [{config['deployment']['port']}]: ").strip()
        if port:
            config['deployment']['port'] = int(port)
        
        workers = input(f"Number of workers [{config['deployment']['workers']}]: ").strip()
        if workers:
            config['deployment']['workers'] = int(workers)
        
        # AD Integration settings
        print("\n2. Active Directory Integration")
        print("-" * 30)
        
        ad_enabled = input(f"Enable AD integration? [{'Y' if config['ad_integration']['enabled'] else 'N'}]: ").strip().lower()
        if ad_enabled in ['y', 'yes', 'n', 'no']:
            config['ad_integration']['enabled'] = ad_enabled in ['y', 'yes']
        
        if config['ad_integration']['enabled']:
            use_mock = input(f"Use mock AD for testing? [{'Y' if config['ad_integration']['use_mock'] else 'N'}]: ").strip().lower()
            if use_mock in ['y', 'yes', 'n', 'no']:
                config['ad_integration']['use_mock'] = use_mock in ['y', 'yes']
            
            if not config['ad_integration']['use_mock']:
                # Ask about authentication mode
                print("\nChoose authentication mode:")
                print("1. Simple bind (like PhotoPrism) - No service account needed")
                print("2. Service account - Full user search and admin group checking")
                
                auth_mode = input("Authentication mode [1/2]: ").strip()
                if auth_mode == "1":
                    config['ad_integration']['simple_bind_mode'] = True
                    print("✓ Simple bind mode selected")
                elif auth_mode == "2":
                    config['ad_integration']['simple_bind_mode'] = False
                    print("✓ Service account mode selected")
                
                server_url = input(f"AD Server URL [{config['ad_integration']['server_url']}]: ").strip()
                if server_url:
                    config['ad_integration']['server_url'] = server_url
                
                domain = input(f"AD Domain [{config['ad_integration']['domain']}]: ").strip()
                if domain:
                    config['ad_integration']['domain'] = domain
                
                if config['ad_integration']['simple_bind_mode']:
                    # Simple bind mode configuration
                    print("\nSimple bind mode configuration:")
                    print("1. {username}@{domain} (e.g., jsmith@company.com)")
                    print("2. {domain}\\{username} (e.g., COMPANY\\jsmith)")
                    print("3. CN={username},{user_base_dn} (e.g., CN=jsmith,OU=Users,DC=company,DC=com)")
                    print("4. Custom pattern")
                    
                    pattern_choice = input("Choose DN pattern [1-4]: ").strip()
                    if pattern_choice == "1":
                        config['ad_integration']['user_dn_pattern'] = '{username}@{domain}'
                    elif pattern_choice == "2":
                        config['ad_integration']['user_dn_pattern'] = '{domain}\\{username}'
                    elif pattern_choice == "3":
                        config['ad_integration']['user_dn_pattern'] = 'CN={username},{user_base_dn}'
                    elif pattern_choice == "4":
                        custom_pattern = input("Enter custom pattern: ").strip()
                        if custom_pattern:
                            config['ad_integration']['user_dn_pattern'] = custom_pattern
                    
                    user_base_dn = input(f"User Base DN [{config['ad_integration']['user_base_dn']}]: ").strip()
                    if user_base_dn:
                        config['ad_integration']['user_base_dn'] = user_base_dn
                    
                    # Admin permissions are managed locally, not from AD groups
                    config['ad_integration']['admin_group'] = ''  # Clear admin group requirement
                    
                    print("\n✓ Simple bind mode configured")
                    print("  - No service account needed")
                    print("  - Users authenticate with their own credentials")
                    print("  - Admin permissions managed locally through application")
                    print("  - No AD group requirements")
                    
                else:
                    # Service account mode configuration
                    bind_dn = input(f"Service Account DN [{config['ad_integration']['bind_dn']}]: ").strip()
                    if bind_dn:
                        config['ad_integration']['bind_dn'] = bind_dn
                    
                    bind_password = input("Service Account Password: ").strip()
                    if bind_password:
                        config['ad_integration']['bind_password'] = bind_password
                    
                    user_base_dn = input(f"User Base DN [{config['ad_integration']['user_base_dn']}]: ").strip()
                    if user_base_dn:
                        config['ad_integration']['user_base_dn'] = user_base_dn
                    
                    print("\nAdmin Group Configuration (Optional):")
                    print("  - Leave empty to manage admin permissions locally")
                    print("  - Or provide AD group DN for automatic admin detection")
                    admin_group = input(f"Admin Group DN [leave empty for local management]: ").strip()
                    if admin_group:
                        config['ad_integration']['admin_group'] = admin_group
                    else:
                        config['ad_integration']['admin_group'] = ''
                    
                    print("\n✓ Service account mode configured")
                    print("  - Full user search and discovery")
                    print("  - Admin permissions managed locally through application")
                    print("  - Service account required")
        
        # Application settings
        print("\n3. Application Settings")
        print("-" * 30)
        
        store_name = input(f"Store name [{config['app_settings']['store_name']}]: ").strip()
        if store_name:
            config['app_settings']['store_name'] = store_name
        
        currency = input(f"Currency symbol [{config['app_settings']['currency_symbol']}]: ").strip()
        if currency:
            config['app_settings']['currency_symbol'] = currency
        
        # Save configuration
        self.save_config(config)
        
        # Generate deployment files
        print("\n4. Generating Deployment Files")
        print("-" * 30)
        
        self.create_production_env(config)
        self.setup_directories(config)
        self.setup_systemd_service(config)
        self.setup_nginx_config(config)
        self.create_deployment_script(config)
        
        print("\n" + "="*60)
        print("Deployment Configuration Complete!")
        print("="*60)
        print("Generated files:")
        print("  - deployment_config.json (configuration)")
        print("  - .env.production (environment variables)")
        print("  - nesop-store.service (systemd service)")
        print("  - nesop-store.nginx (nginx configuration)")
        print("  - deploy.sh (deployment script)")
        print("\nTo deploy to your server:")
        print("  1. Copy all files to your server")
        print("  2. Run: sudo ./deploy.sh")
        print("  3. Access the application at your server's IP")
        print("  4. Login with: fallback_admin / ChangeMe123!")
        print("="*60)
        
        return config

def main():
    """Main deployment setup function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NESOP Store Deployment Configuration')
    parser.add_argument('--setup-db', action='store_true', help='Setup production database')
    parser.add_argument('--interactive', action='store_true', help='Interactive setup')
    parser.add_argument('--config-file', default='deployment_config.json', help='Configuration file path')
    
    args = parser.parse_args()
    
    deploy_config = DeploymentConfig(args.config_file)
    
    if args.setup_db:
        config = deploy_config.load_config()
        deploy_config.setup_database(config)
    elif args.interactive:
        deploy_config.interactive_setup()
    else:
        # Default behavior - run interactive setup
        deploy_config.interactive_setup()

if __name__ == '__main__':
    main() 