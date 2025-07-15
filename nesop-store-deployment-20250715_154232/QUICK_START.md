# NESOP Store - Quick Start Guide

## Package Information
- Created: 2025-07-15 15:42:32
- Version: 1.0.0
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
scp -r nesop-store-deployment-20250715_154232/ user@your-server:/tmp/
ssh user@your-server
cd /tmp/nesop-store-deployment-20250715_154232
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
- Test AD user login
- Test admin panel access
- Test AD user search/import
- Verify all functionality works

## Files Overview
- `server.py` - Main Flask application
- `deploy_config.py` - Deployment configuration wizard
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

## Security Notes
- Deploy on internal network only
- Use LDAPS for AD connections
- Change default passwords
- Regular security updates

Generated: 2025-07-15 15:42:32
