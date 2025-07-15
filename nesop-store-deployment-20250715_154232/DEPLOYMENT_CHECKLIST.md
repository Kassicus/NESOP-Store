# NESOP Store - Deployment Checklist

## Pre-Deployment Preparation

### Server Requirements
- [ ] Server has Ubuntu 20.04 LTS or newer
- [ ] Server has minimum 2GB RAM (4GB recommended)
- [ ] Server has 10GB available disk space
- [ ] Server has network access to Active Directory (if using real AD)
- [ ] Server has Python 3.8 or newer installed
- [ ] Server has root/sudo access available

### Network Configuration
- [ ] Internal network access configured
- [ ] Firewall rules configured (if applicable)
- [ ] DNS resolution working
- [ ] Active Directory server accessible (if using real AD)

### Active Directory Preparation (if using real AD)
- [ ] Service account created in Active Directory
- [ ] Service account has "Read" permissions to user search base
- [ ] Admin group created and configured
- [ ] Service account password documented securely
- [ ] LDAP/LDAPS connectivity tested

## Deployment Process

### 1. File Transfer
- [ ] All application files copied to server
- [ ] Files placed in `/opt/nesop-store/` directory
- [ ] File ownership and permissions verified

### 2. System Dependencies
- [ ] Python 3 and pip installed
- [ ] Virtual environment support available
- [ ] Nginx web server installed
- [ ] Systemd service management available
- [ ] SQLite3 available (usually included with Python)

### 3. Application Setup
- [ ] Application user `nesop` created
- [ ] Virtual environment created successfully
- [ ] Python dependencies installed from requirements.txt
- [ ] No dependency installation errors

### 4. Configuration
- [ ] Deployment configuration script executed
- [ ] Configuration file `deployment_config.json` created
- [ ] Environment file `.env.production` created
- [ ] Secret key generated and configured
- [ ] Active Directory settings configured (if applicable)
- [ ] Database path configured
- [ ] Application settings configured

### 5. Database Setup
- [ ] Production database created
- [ ] Database migration completed successfully
- [ ] Fallback admin user created
- [ ] Database file permissions correct
- [ ] Database connection tested

### 6. Service Configuration
- [ ] Systemd service file created
- [ ] Service file installed in `/etc/systemd/system/`
- [ ] Service enabled for auto-start
- [ ] Service daemon reloaded

### 7. Web Server Configuration
- [ ] Nginx configuration file created
- [ ] Nginx configuration installed
- [ ] Nginx configuration syntax tested
- [ ] Nginx restarted successfully

### 8. Service Startup
- [ ] NESOP Store service started
- [ ] Service status verified as active
- [ ] No service startup errors in logs
- [ ] Application responding on configured port

## Post-Deployment Verification

### Basic Functionality
- [ ] Web interface accessible via browser
- [ ] Login page displays correctly
- [ ] Fallback admin login works (fallback_admin / ChangeMe123!)
- [ ] Admin panel accessible
- [ ] Store front page loads correctly

### Active Directory Integration (if enabled)
- [ ] AD users can be searched in admin panel
- [ ] AD user authentication works
- [ ] AD users can be imported successfully
- [ ] Admin roles detected correctly from AD groups
- [ ] AD audit logging working

### Database Operations
- [ ] User management functions work
- [ ] Product management functions work
- [ ] Currency operations work
- [ ] Database writes are successful
- [ ] Data persistence verified

### File Operations
- [ ] Image uploads work correctly
- [ ] Images display properly
- [ ] File permissions correct
- [ ] Upload directory writable

### Logging and Monitoring
- [ ] Application logs being written
- [ ] Log rotation configured
- [ ] Error logs accessible
- [ ] System service logs available

## Security Verification

### Access Control
- [ ] Default admin password changed
- [ ] Service account passwords secured
- [ ] File permissions restricted appropriately
- [ ] Database access restricted

### Network Security
- [ ] Application only accessible from internal network
- [ ] Unnecessary ports closed
- [ ] SSL/TLS configured for AD (if applicable)
- [ ] Web server security headers configured

### Operational Security
- [ ] Backup procedures documented
- [ ] Log monitoring configured
- [ ] Update procedures documented
- [ ] Incident response plan available

## Final Steps

### Documentation
- [ ] Deployment configuration documented
- [ ] Admin credentials documented securely
- [ ] Backup procedures documented
- [ ] Monitoring procedures documented
- [ ] Troubleshooting guide available

### Handover
- [ ] System administrator trained
- [ ] Admin users trained
- [ ] Documentation provided
- [ ] Support contacts provided
- [ ] Maintenance schedule established

### Testing
- [ ] User acceptance testing completed
- [ ] Performance testing completed (if applicable)
- [ ] Backup and restore tested
- [ ] Failover procedures tested (if applicable)

## Rollback Plan

### If Deployment Fails
- [ ] Stop all services
- [ ] Remove application files
- [ ] Remove service configurations
- [ ] Remove database files
- [ ] Restore previous configuration (if updating)

### Emergency Contacts
- [ ] Technical support contact documented
- [ ] System administrator contact documented
- [ ] Active Directory administrator contact documented
- [ ] Management escalation contact documented

## Sign-off

### Technical Verification
- [ ] **Deployed by**: _________________ **Date**: _________
- [ ] **Tested by**: _________________ **Date**: _________
- [ ] **Approved by**: _________________ **Date**: _________

### Notes
```
Deployment Notes:
- Any issues encountered:
- Performance observations:
- Security considerations:
- Recommendations:
```

---

**Deployment Status**: 
- [ ] **SUCCESSFUL** - All checks passed, system operational
- [ ] **PARTIAL** - Some issues, requires attention
- [ ] **FAILED** - Critical issues, deployment unsuccessful

**Final Verification Date**: __________

**System Ready for Production**: [ ] YES [ ] NO 