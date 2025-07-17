# NESOP Store - Update System Guide

## Overview

The NESOP Store update system allows you to deploy updates to your production application without requiring full redeployment. This system provides:

- **Lightweight update packages** (smaller than full deployment packages)
- **Automated backup creation** before updates
- **Rollback capability** if updates fail
- **Database migration support**
- **Service restart management**
- **Update validation** to ensure success

## System Architecture

### Components

1. **`create_update_package.py`** - Creates update packages from your development environment
2. **`update_manager.py`** - Applies updates on the server (installed on production server)
3. **`validate_update.py`** - Validates that updates were applied correctly
4. **Update packages** - Compressed archives containing changed files and migration scripts

### Update Flow

```
[Development] → [Create Update Package] → [Transfer to Server] → [Apply Update] → [Validate]
```

## Prerequisites

### Development Environment
- Python 3.8+
- All your latest application code
- Access to create update packages

### Production Server
- NESOP Store already deployed and running
- `update_manager.py` installed in the application directory
- Root/sudo access for applying updates

## Creating Update Packages

### Basic Update Package

Create a standard update package with all commonly changed files:

```bash
# Create update package with auto-detected files
python3 create_update_package.py

# Create update package with specific version
python3 create_update_package.py --version 1.0.5
```

### Custom Update Package

Create update package with specific files:

```bash
# Include only specific files
python3 create_update_package.py --files server.py admin.html config.py

# Create update without migration scripts
python3 create_update_package.py --no-migrations
```

### Package Contents

Update packages typically include:
- **Core files**: `server.py`, `db_utils.py`, `ad_utils.py`, `config.py`
- **Frontend files**: `index.html`, `admin.html`, `cart.html`, `register.html`
- **Asset directories**: `scripts/`, `styles/`, `assets/`
- **Migration scripts**: Database migration files (if included)
- **Utilities**: `validate_deployment.py`, `requirements.txt`
- **Manifest**: `update_manifest.json` with update metadata

## Applying Updates

### Transfer Update to Server

1. **Copy update package to server**:
   ```bash
   scp nesop-store-update-20250717_123456.tar.gz user@your-server:/tmp/
   ```

2. **Extract on server**:
   ```bash
   ssh user@your-server
   cd /tmp
   tar -xzf nesop-store-update-20250717_123456.tar.gz
   ```

### Apply Update

Run the update manager as root:

```bash
cd /tmp/nesop-store-update-20250717_123456
sudo python3 /opt/nesop-store/update_manager.py apply .
```

### Update Process

The update manager will:
1. **Validate** the update package
2. **Create backup** of current application
3. **Stop** the application service
4. **Apply** file and directory updates
5. **Run** database migrations (if included)
6. **Restart** the application service
7. **Validate** the service is running
8. **Log** the update results

## Validation

### Automatic Validation

After applying an update, run validation:

```bash
sudo python3 /opt/nesop-store/validate_update.py
```

### Validation Checks

The validator performs these checks:
- **File existence**: Verifies all essential files are present
- **Service status**: Confirms the service is running
- **Database connection**: Tests database connectivity
- **Web application**: Validates HTTP responses
- **File permissions**: Checks file ownership
- **Configuration**: Validates config files
- **Update history**: Reviews update logs

### Specific Validation

Run individual validation checks:

```bash
# Check only service status
sudo python3 /opt/nesop-store/validate_update.py --check service

# Check only web application
sudo python3 /opt/nesop-store/validate_update.py --check web
```

## Backup and Rollback

### Automatic Backups

Every update automatically creates a backup before applying changes. Backups are stored in `/opt/nesop-store/backups/` with timestamps.

### Manual Backup

Create a manual backup:

```bash
sudo python3 /opt/nesop-store/update_manager.py status
```

### List Available Backups

```bash
sudo python3 /opt/nesop-store/update_manager.py list-backups
```

### Rollback to Previous Version

```bash
sudo python3 /opt/nesop-store/update_manager.py rollback backup_name
```

Example:
```bash
sudo python3 /opt/nesop-store/update_manager.py rollback pre_update_20250717_123456
```

## Common Update Scenarios

### 1. Bug Fix Update

For simple bug fixes in application code:

```bash
# Development environment
python3 create_update_package.py --files server.py --no-migrations

# Production server
sudo python3 /opt/nesop-store/update_manager.py apply /tmp/update-package/
sudo python3 /opt/nesop-store/validate_update.py
```

### 2. Frontend Update

For changes to web interface:

```bash
# Development environment
python3 create_update_package.py --files index.html admin.html --no-migrations

# Production server
sudo python3 /opt/nesop-store/update_manager.py apply /tmp/update-package/
sudo python3 /opt/nesop-store/validate_update.py --check web
```

### 3. Database Schema Update

For changes requiring database migrations:

```bash
# Development environment
python3 create_update_package.py --version 1.0.5

# Production server
sudo python3 /opt/nesop-store/update_manager.py apply /tmp/update-package/
sudo python3 /opt/nesop-store/validate_update.py --check database
```

### 4. Configuration Update

For changes to configuration or dependencies:

```bash
# Development environment
python3 create_update_package.py --files config.py requirements.txt

# Production server
sudo python3 /opt/nesop-store/update_manager.py apply /tmp/update-package/
sudo python3 /opt/nesop-store/validate_update.py --check config
```

## Troubleshooting

### Update Failed

If an update fails, the system will automatically attempt to rollback:

```bash
# Check what went wrong
sudo journalctl -u nesop-store -f

# Check update logs
sudo tail -f /opt/nesop-store/logs/update.log

# Manual rollback if needed
sudo python3 /opt/nesop-store/update_manager.py list-backups
sudo python3 /opt/nesop-store/update_manager.py rollback backup_name
```

### Service Not Starting

```bash
# Check service status
sudo systemctl status nesop-store

# Check application logs
sudo journalctl -u nesop-store -f

# Restart service manually
sudo systemctl restart nesop-store
```

### Database Issues

```bash
# Check database connectivity
sudo python3 /opt/nesop-store/validate_update.py --check database

# Run migrations manually
cd /opt/nesop-store
sudo python3 migrate_ad_integration.py
```

### Permission Issues

```bash
# Fix file permissions
sudo chown -R nesop:nesop /opt/nesop-store/
sudo chmod +x /opt/nesop-store/*.py
```

## Best Practices

### Before Creating Updates

1. **Test thoroughly** in development
2. **Backup your work** before creating packages
3. **Review changes** to ensure only necessary files are included
4. **Test migrations** if database changes are involved

### Before Applying Updates

1. **Verify system is healthy**:
   ```bash
   sudo python3 /opt/nesop-store/validate_update.py
   ```

2. **Check disk space**:
   ```bash
   df -h /opt/nesop-store
   ```

3. **Review update contents**:
   ```bash
   # Check update manifest
   cat /tmp/update-package/update_manifest.json
   ```

### After Updates

1. **Validate immediately**:
   ```bash
   sudo python3 /opt/nesop-store/validate_update.py
   ```

2. **Monitor logs**:
   ```bash
   sudo tail -f /opt/nesop-store/logs/nesop_store.log
   ```

3. **Test functionality**:
   - Visit the application in browser
   - Test admin login
   - Test AD integration (if applicable)

## Advanced Features

### Custom Validation

Add custom validation checks by extending `validate_update.py`:

```python
def validate_custom_feature(self):
    """Custom validation for specific features"""
    # Your validation logic here
    return True
```

### Update Scheduling

Use cron for scheduled updates:

```bash
# Add to crontab for automated updates
0 2 * * 0 /path/to/update_script.sh
```

### Monitoring Integration

The update system logs all activities to:
- `/opt/nesop-store/logs/update.log` - Update operations
- `/opt/nesop-store/logs/update_history.json` - Update history
- System journal via `journalctl -u nesop-store`

## Security Considerations

1. **Verify update sources** - Only apply updates from trusted sources
2. **Hash validation** - Update packages include file hashes for integrity
3. **Permission checks** - Updates maintain proper file permissions
4. **Backup retention** - Keep backups for rollback capability
5. **Log monitoring** - Review update logs for security events

## Update History

The system maintains a complete history of all updates in `/opt/nesop-store/logs/update_history.json`. Each entry includes:

- Timestamp
- Update version
- Files updated
- Migrations run
- Backup created
- Status (success/failure)

## Support

For issues with the update system:

1. Check the logs in `/opt/nesop-store/logs/`
2. Run validation to identify problems
3. Review this guide for common scenarios
4. Use rollback if the update caused issues

---

*This update system is designed to be safe, reliable, and easy to use. Always test updates in a staging environment before applying to production.* 