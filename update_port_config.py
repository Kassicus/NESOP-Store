#!/usr/bin/env python3
"""
NESOP Store Port Configuration Update Helper
Updates port configuration for production deployment without full redeployment.
"""

import os
import sys
import json
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PortConfigUpdater:
    """Handles updating port configuration for NESOP Store"""
    
    def __init__(self, app_path="/opt/nesop-store"):
        self.app_path = Path(app_path)
        self.config_file = self.app_path / "deployment_config.json"
        self.env_file = self.app_path / ".env.production"
        self.nginx_config = "/etc/nginx/sites-available/nesop-store"
        self.service_name = "nesop-store"
        
    def backup_configs(self):
        """Create backup of current configuration files"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = self.app_path / "backups" / f"config_backup_{timestamp}"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        configs_to_backup = [
            self.config_file,
            self.env_file,
            Path(self.nginx_config) if Path(self.nginx_config).exists() else None
        ]
        
        for config in configs_to_backup:
            if config and config.exists():
                backup_file = backup_dir / config.name
                import shutil
                shutil.copy2(config, backup_file)
                logger.info(f"Backed up: {config} -> {backup_file}")
        
        return backup_dir
    
    def update_deployment_config(self, new_port):
        """Update the deployment_config.json file with new port"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                
                # Update port in deployment section
                if 'deployment' not in config:
                    config['deployment'] = {}
                
                old_port = config['deployment'].get('port', 8080)
                config['deployment']['port'] = new_port
                
                # Save updated config
                with open(self.config_file, 'w') as f:
                    json.dump(config, f, indent=2)
                
                logger.info(f"Updated deployment_config.json: port {old_port} -> {new_port}")
                return True
            else:
                logger.warning(f"Config file not found: {self.config_file}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating deployment config: {e}")
            return False
    
    def update_env_file(self, new_port):
        """Update the .env.production file with new port"""
        try:
            env_content = []
            port_updated = False
            
            if self.env_file.exists():
                with open(self.env_file, 'r') as f:
                    lines = f.readlines()
                
                for line in lines:
                    if line.startswith('DEPLOYMENT_PORT='):
                        old_port = line.split('=')[1].strip()
                        env_content.append(f'DEPLOYMENT_PORT={new_port}\n')
                        port_updated = True
                        logger.info(f"Updated .env.production: DEPLOYMENT_PORT {old_port} -> {new_port}")
                    else:
                        env_content.append(line)
            
            # Add DEPLOYMENT_PORT if it wasn't found
            if not port_updated:
                env_content.append(f'DEPLOYMENT_PORT={new_port}\n')
                logger.info(f"Added DEPLOYMENT_PORT={new_port} to .env.production")
            
            # Write updated env file
            with open(self.env_file, 'w') as f:
                f.writelines(env_content)
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating env file: {e}")
            return False
    
    def generate_nginx_config(self, new_port, server_name=None):
        """Generate new nginx configuration with updated port"""
        if not server_name:
            server_name = "your-internal-server.yourdomain.com"
        
        nginx_content = f"""server {{
    listen 80;
    server_name {server_name};
    
    # Optional: Redirect to HTTPS
    # return 301 https://$server_name$request_uri;
    
    location / {{
        proxy_pass http://127.0.0.1:{new_port};
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
        alias /opt/nesop-store/assets/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }}
    
    location /static/ {{
        alias /opt/nesop-store/static/;
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
"""
        
        # Write nginx config to app directory for manual installation
        nginx_file = self.app_path / "nesop-store.nginx"
        with open(nginx_file, 'w') as f:
            f.write(nginx_content)
        
        logger.info(f"Generated nginx config: {nginx_file}")
        logger.info(f"To install: sudo cp {nginx_file} /etc/nginx/sites-available/nesop-store")
        logger.info("Then: sudo nginx -t && sudo systemctl reload nginx")
        
        return nginx_file
    
    def restart_service(self):
        """Restart the NESOP Store service"""
        try:
            logger.info(f"Restarting {self.service_name} service...")
            result = subprocess.run(['systemctl', 'restart', self.service_name], 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"✓ Service {self.service_name} restarted successfully")
                
                # Wait a moment and check status
                import time
                time.sleep(2)
                
                status_result = subprocess.run(['systemctl', 'is-active', self.service_name], 
                                             capture_output=True, text=True)
                
                if status_result.stdout.strip() == 'active':
                    logger.info(f"✓ Service {self.service_name} is running")
                    return True
                else:
                    logger.error(f"✗ Service {self.service_name} failed to start")
                    return False
            else:
                logger.error(f"✗ Failed to restart service: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error restarting service: {e}")
            return False
    
    def validate_port_change(self, new_port):
        """Validate that the port change was successful"""
        try:
            import socket
            import time
            
            # Wait for service to start
            logger.info(f"Validating port {new_port} is accessible...")
            time.sleep(3)
            
            # Check if port is listening
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex(('127.0.0.1', new_port))
            sock.close()
            
            if result == 0:
                logger.info(f"✓ Port {new_port} is accessible")
                return True
            else:
                logger.error(f"✗ Port {new_port} is not accessible")
                return False
                
        except Exception as e:
            logger.error(f"Error validating port: {e}")
            return False
    
    def update_port(self, new_port, server_name=None, restart=True):
        """Main method to update port configuration"""
        logger.info(f"Starting port configuration update to {new_port}")
        logger.info("=" * 50)
        
        # Validate port choice for nginx setup
        if new_port == 80 or new_port == 443:
            logger.warning(f"Port {new_port} is typically used by web servers like nginx.")
            logger.warning("For reverse proxy setup, your Flask app should use an internal port like 8080, 5000, etc.")
            logger.warning("Nginx will listen on port 80/443 and proxy to your Flask app's internal port.")
            
            response = input("Do you want to continue with port 80/443? This may conflict with nginx. (y/N): ")
            if response.lower() != 'y':
                logger.info("Port update cancelled. Consider using an internal port like 8080.")
                return False
        
        # Create backup
        backup_dir = self.backup_configs()
        logger.info(f"Configuration backup created: {backup_dir}")
        
        # Update configurations
        success = True
        
        # Update deployment config
        if not self.update_deployment_config(new_port):
            success = False
        
        # Update environment file
        if not self.update_env_file(new_port):
            success = False
        
        # Generate nginx config
        nginx_file = self.generate_nginx_config(new_port, server_name)
        
        if not success:
            logger.error("Configuration update failed. Check logs above.")
            return False
        
        # Restart service if requested
        if restart:
            if not self.restart_service():
                logger.error("Service restart failed. Configuration updated but service may need manual restart.")
                return False
            
            # Validate the change
            if not self.validate_port_change(new_port):
                logger.warning("Port validation failed. Service may still be starting.")
        
        logger.info("=" * 50)
        logger.info("PORT CONFIGURATION UPDATE COMPLETE!")
        logger.info("=" * 50)
        logger.info(f"✓ Port updated to: {new_port}")
        logger.info(f"✓ Configuration backup: {backup_dir}")
        logger.info(f"✓ Nginx config generated: {nginx_file}")
        
        if restart:
            logger.info(f"✓ Service restarted: {self.service_name}")
        
        logger.info("\nNext steps:")
        if new_port == 80 or new_port == 443:
            logger.warning("⚠️  IMPORTANT: You configured your Flask app to use port 80/443!")
            logger.warning("   This may conflict with nginx. Consider these options:")
            logger.warning("   1. Change your app to use an internal port (8080, 5000, etc.)")
            logger.warning("   2. Don't install the nginx config if running Flask directly on port 80")
            logger.warning("   3. Use nginx on a different port if you want reverse proxy")
        else:
            logger.info(f"1. Install nginx config: sudo cp {nginx_file} /etc/nginx/sites-available/nesop-store")
            logger.info("2. Test nginx: sudo nginx -t")
            logger.info("3. Reload nginx: sudo systemctl reload nginx")
            logger.info(f"4. Test access: http://your-server/ (nginx will proxy to port {new_port})")
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Update NESOP Store port configuration')
    parser.add_argument('port', type=int, help='New port number (e.g., 80, 8080, 5000)')
    parser.add_argument('--server-name', '-s', help='Server name for nginx config')
    parser.add_argument('--no-restart', action='store_true', help='Skip service restart')
    parser.add_argument('--app-path', '-p', default='/opt/nesop-store', 
                       help='Path to NESOP Store application')
    
    args = parser.parse_args()
    
    # Validate port
    if not (1 <= args.port <= 65535):
        logger.error("Port must be between 1 and 65535")
        sys.exit(1)
    
    # Check if running as root for service operations
    if not args.no_restart and os.geteuid() != 0:
        logger.error("This script must be run as root (sudo) to restart services")
        sys.exit(1)
    
    try:
        updater = PortConfigUpdater(args.app_path)
        success = updater.update_port(
            args.port, 
            args.server_name, 
            restart=not args.no_restart
        )
        
        if success:
            logger.info("Port configuration update completed successfully!")
            sys.exit(0)
        else:
            logger.error("Port configuration update failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Update cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 