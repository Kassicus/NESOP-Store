# NESOP Store - Quick Start Guide

## Package Information
- Created: 2025-07-17 12:36:07
- Version: 1.0.5
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
scp -r nesop-store-deployment-20250717_123607/ user@your-server:/tmp/
ssh user@your-server
cd /tmp/nesop-store-deployment-20250717_123607
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

# If you have existing users, run migration to fix duplicates
python3 migrate_username_normalization.py
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
- `migrate_username_normalization.py` - Username normalization and duplicate user merger
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

## Recent Improvements (v1.0.5)
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
- Added username normalization to prevent duplicate users with different formats
- Created migration script to merge existing duplicate user accounts

## Security Notes
- Deploy on internal network only
- Use LDAPS for AD connections
- Change default passwords immediately
- Regular security updates
- Run validation after deployment

Generated: 2025-07-17 12:36:07
