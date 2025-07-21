# NESOP Store - Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the NESOP Store application on an internal server with Active Directory integration.

## Prerequisites

### System Requirements
- Ubuntu 20.04 LTS or newer (recommended)
- Python 3.8 or newer
- 2GB RAM minimum (4GB recommended)
- 10GB available disk space
- Network access to your Active Directory server

### Software Dependencies
- Python 3 and pip
- Virtual environment support
- Nginx web server
- Systemd for service management
- SQLite3 (included with Python)

## Quick Deployment

### 1. Download and Extract
```bash
# Download the application files to your server
# Copy all files to /opt/nesop-store
sudo mkdir -p /opt/nesop-store
sudo cp -r * /opt/nesop-store/
cd /opt/nesop-store
```

### 2. Run Deployment Configuration
```bash
# Run the interactive deployment setup
python3 deploy_config.py

# Or run with specific options
python3 deploy_config.py --interactive
```

### 3. Execute Deployment Script
```bash
# Make deployment script executable and run it
chmod +x deploy.sh
sudo ./deploy.sh
```

### 4. Verify Deployment
```bash
# Check if services are running
sudo systemctl status nesop-store
sudo systemctl status nginx

# Check application logs
sudo journalctl -u nesop-store -f
```

## Manual Deployment

### 1. System Setup
```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install required system packages
sudo apt install -y python3 python3-pip python3-venv nginx supervisor git

# Create application user
sudo useradd -r -s /bin/false nesop
sudo mkdir -p /opt/nesop-store
sudo chown nesop:nesop /opt/nesop-store
```

### 2. Application Setup
```bash
# Copy application files
sudo cp -r . /opt/nesop-store/
sudo chown -R nesop:nesop /opt/nesop-store/

# Create virtual environment
cd /opt/nesop-store
sudo -u nesop python3 -m venv venv
sudo -u nesop venv/bin/pip install --upgrade pip
sudo -u nesop venv/bin/pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Initialize the database
sudo -u nesop venv/bin/python3 deploy_config.py --setup-db

# Verify database creation
sudo -u nesop ls -la nesop_store_production.db
```

### 4. Configuration Setup
```bash
# Run configuration setup
sudo -u nesop venv/bin/python3 deploy_config.py --interactive

# This will create:
# - deployment_config.json
# - .env.production
# - nesop-store.service
# - nesop-store.nginx
# - deploy.sh
```

### 5. Service Configuration
```bash
# Install systemd service
sudo cp nesop-store.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nesop-store

# Configure nginx
sudo cp nesop-store.nginx /etc/nginx/sites-available/nesop-store
sudo ln -sf /etc/nginx/sites-available/nesop-store /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Start Services
```bash
# Start the application
sudo systemctl start nesop-store
sudo systemctl status nesop-store

# Check if nginx is running
sudo systemctl status nginx
```

## Configuration Options

### Environment Variables
The application uses the following environment variables (configured in `.env.production`):

#### Flask Configuration
- `FLASK_ENV`: Application environment (production)
- `SECRET_KEY`: Flask secret key (auto-generated)
- `DEBUG`: Debug mode (false for production)

#### Database Configuration
- `DATABASE_PATH`: Path to SQLite database file
- `BACKUP_ENABLED`: Enable automatic backups (true/false)

#### AD Integration
- `AD_ENABLED`: Enable Active Directory integration (true/false)
- `AD_USE_MOCK`: Use mock AD for testing (true/false)
- `AD_SERVER_URL`: LDAP server URL (e.g., ldap://dc.company.com)
- `AD_DOMAIN`: Active Directory domain
- `AD_BIND_DN`: Service account distinguished name
- `AD_BIND_PASSWORD`: Service account password
- `AD_USER_BASE_DN`: User search base DN
- `AD_ADMIN_GROUP`: Admin group DN
- `AD_USE_SSL`: Use SSL/TLS for LDAP (true/false)
- `AD_PORT`: LDAP port (389 for non-SSL, 636 for SSL)
- `AD_TIMEOUT`: Connection timeout in seconds

#### Application Settings
- `STORE_NAME`: Display name for the store
- `CURRENCY_SYMBOL`: Currency symbol (₦, €, $, etc.)
- `MAX_FILE_SIZE`: Maximum upload file size in bytes
- `UPLOAD_PATH`: Path for uploaded files
- `SESSION_LIFETIME`: Session timeout in seconds

#### Logging
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE`: Log file name
- `LOG_MAX_SIZE`: Maximum log file size in bytes
- `LOG_BACKUP_COUNT`: Number of backup log files to keep

### Active Directory Configuration

#### Service Account Setup
1. Create a service account in Active Directory
2. Grant the account "Read" permissions to the user search base
3. Configure the account credentials in the deployment configuration

#### Admin Group Setup
1. Create a security group for NESOP Store admins
2. Add users who should have admin access to this group
3. Configure the group DN in the deployment configuration

#### Example AD Configuration
```env
AD_ENABLED=true
AD_USE_MOCK=false
AD_SERVER_URL=ldap://dc.company.com
AD_DOMAIN=company.com
AD_BIND_DN=CN=nesop_service,OU=Service Accounts,DC=company,DC=com
AD_BIND_PASSWORD=YourServiceAccountPassword
AD_USER_BASE_DN=OU=Users,DC=company,DC=com
AD_ADMIN_GROUP=CN=NESOP_Admins,OU=Groups,DC=company,DC=com
AD_USE_SSL=true
AD_PORT=636
AD_TIMEOUT=10
```

## Security Considerations

### Network Security
- Deploy on internal network only
- Use firewall rules to restrict access
- Consider using HTTPS with internal certificates

### Application Security
- Change default admin password immediately
- Use strong passwords for service accounts
- Regularly update the application and dependencies
- Monitor application logs for suspicious activity

### Database Security
- Regular database backups
- Restrict file system permissions
- Consider database encryption for sensitive data

### AD Security
- Use least-privilege service accounts
- Enable LDAP over SSL/TLS
- Regularly rotate service account passwords
- Monitor AD logs for authentication attempts

## Monitoring and Maintenance

### Log Files
- Application logs: `/opt/nesop-store/logs/nesop_store.log`
- Nginx access logs: `/var/log/nginx/nesop-store.access.log`
- Nginx error logs: `/var/log/nginx/nesop-store.error.log`
- System logs: `journalctl -u nesop-store`

### Health Checks
```bash
# Check application status
sudo systemctl status nesop-store

# Check if application is responding
curl -I http://localhost:8080/

# Check database connectivity
sudo -u nesop /opt/nesop-store/venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('/opt/nesop-store/nesop_store_production.db')
print('Database OK')
conn.close()
"

# Check AD connectivity (if enabled)
sudo -u nesop /opt/nesop-store/venv/bin/python3 -c "
import os
os.environ['AD_ENABLED'] = 'true'
import ad_utils
ad_manager = ad_utils.ActiveDirectoryManager()
print('AD connection OK')
"
```

### Backup Procedures
```bash
# Database backup
sudo -u nesop cp /opt/nesop-store/nesop_store_production.db \
    /opt/nesop-store/backups/nesop_store_$(date +%Y%m%d_%H%M%S).db

# Configuration backup
sudo -u nesop tar -czf /opt/nesop-store/backups/config_$(date +%Y%m%d_%H%M%S).tar.gz \
    deployment_config.json .env.production

# Full application backup
sudo tar -czf /opt/nesop-store/backups/app_$(date +%Y%m%d_%H%M%S).tar.gz \
    --exclude=backups --exclude=logs --exclude=venv /opt/nesop-store/
```

### Updates and Maintenance
```bash
# Stop services
sudo systemctl stop nesop-store

# Backup current installation
sudo tar -czf /opt/nesop-store-backup-$(date +%Y%m%d).tar.gz /opt/nesop-store/

# Update application code
# ... copy new files ...

# Update dependencies
sudo -u nesop /opt/nesop-store/venv/bin/pip install -r requirements.txt

# Run database migrations if needed
sudo -u nesop /opt/nesop-store/venv/bin/python3 migrate_ad_integration.py

# Restart services
sudo systemctl start nesop-store
sudo systemctl status nesop-store
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check service status
sudo systemctl status nesop-store

# Check logs
sudo journalctl -u nesop-store --no-pager -l

# Check configuration
sudo -u nesop /opt/nesop-store/venv/bin/python3 deploy_config.py --setup-db
```

#### Database Issues
```bash
# Check database file permissions
ls -la /opt/nesop-store/nesop_store_production.db

# Test database connection
sudo -u nesop /opt/nesop-store/venv/bin/python3 -c "
import sqlite3
conn = sqlite3.connect('/opt/nesop-store/nesop_store_production.db')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM users')
print('Users count:', cursor.fetchone()[0])
conn.close()
"
```

#### AD Connection Issues
```bash
# Test AD connectivity
sudo -u nesop /opt/nesop-store/venv/bin/python3 -c "
import os
os.environ['AD_ENABLED'] = 'true'
import ad_utils
ad_manager = ad_utils.ActiveDirectoryManager()
print('AD Manager initialized')
"

# Check AD configuration
grep AD_ /opt/nesop-store/.env.production
```

#### Web Server Issues
```bash
# Check nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/nesop-store.error.log

# Test direct application access
curl -I http://localhost:8080/
```

### Support and Documentation
- Check application logs for error messages
- Review the deployment configuration
- Verify network connectivity to AD server
- Test with mock AD if real AD is not available

## Default Credentials
- **Username**: `fallback_admin`
- **Password**: `ChangeMe123!`

**Important**: Change the default password immediately after first login!

## Performance Tuning

### Application Performance
- Adjust worker count based on server resources
- Monitor memory usage and adjust accordingly
- Consider using Redis for session storage in high-traffic scenarios

### Database Performance
- Regular database maintenance and optimization
- Consider moving to PostgreSQL for larger installations
- Implement database connection pooling if needed

### Network Performance
- Use CDN for static assets if serving external users
- Enable gzip compression in nginx
- Optimize image uploads and storage

## Scaling Considerations
- Load balancing with multiple application instances
- Database clustering or replication
- Caching strategies with Redis or Memcached
- Monitoring and alerting systems 