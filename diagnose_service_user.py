#!/usr/bin/env python3
"""
NESOP Store - Service User Diagnostic Script
Identifies exactly what user the Flask service runs as and diagnoses permission issues.
"""

import os
import stat
import sys
import logging
import grp
import pwd
import subprocess
from pathlib import Path

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def diagnose_service_user():
    """Comprehensive diagnosis of service user and permissions"""
    logger = setup_logging()
    
    logger.info("NESOP Store - Service User Diagnostic")
    logger.info("=" * 60)
    
    # Current script execution context
    logger.info("1. CURRENT SCRIPT EXECUTION CONTEXT:")
    current_uid = os.getuid()
    current_gid = os.getgid()
    
    try:
        current_user = pwd.getpwuid(current_uid).pw_name
    except KeyError:
        current_user = str(current_uid)
    
    try:
        current_group = grp.getgrgid(current_gid).gr_name
    except KeyError:
        current_group = str(current_gid)
    
    logger.info(f"   Script running as: {current_user}:{current_group} ({current_uid}:{current_gid})")
    logger.info(f"   Is root: {'Yes' if current_uid == 0 else 'No'}")
    logger.info("")
    
    # Service configuration analysis
    logger.info("2. SERVICE CONFIGURATION ANALYSIS:")
    
    service_info = {}
    
    # Get service file content
    try:
        with open('/etc/systemd/system/nesop-store.service', 'r') as f:
            service_content = f.read()
        
        logger.info("   Service file found: /etc/systemd/system/nesop-store.service")
        
        # Extract key information
        for line in service_content.split('\n'):
            line = line.strip()
            if line.startswith('User='):
                service_info['user'] = line.split('=', 1)[1]
            elif line.startswith('Group='):
                service_info['group'] = line.split('=', 1)[1]
            elif line.startswith('WorkingDirectory='):
                service_info['working_dir'] = line.split('=', 1)[1]
            elif line.startswith('ExecStart='):
                service_info['exec_start'] = line.split('=', 1)[1]
        
        logger.info(f"   Service User: {service_info.get('user', 'NOT SET')}")
        logger.info(f"   Service Group: {service_info.get('group', 'NOT SET')}")
        logger.info(f"   Working Directory: {service_info.get('working_dir', 'NOT SET')}")
        logger.info(f"   Exec Start: {service_info.get('exec_start', 'NOT SET')}")
        
    except FileNotFoundError:
        logger.error("   ✗ Service file not found: /etc/systemd/system/nesop-store.service")
    except Exception as e:
        logger.error(f"   ✗ Error reading service file: {e}")
    
    logger.info("")
    
    # Runtime service information
    logger.info("3. RUNTIME SERVICE INFORMATION:")
    
    try:
        # Get service status
        result = subprocess.run(['systemctl', 'status', 'nesop-store', '--no-pager'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("   Service Status: ACTIVE")
        else:
            logger.warning("   Service Status: NOT ACTIVE")
        
        # Get service properties
        properties = ['User', 'Group', 'MainPID', 'WorkingDirectory']
        for prop in properties:
            try:
                result = subprocess.run(['systemctl', 'show', 'nesop-store', f'--property={prop}'], 
                                      capture_output=True, text=True)
                if result.returncode == 0 and '=' in result.stdout:
                    value = result.stdout.strip().split('=', 1)[1]
                    logger.info(f"   {prop}: {value}")
            except Exception:
                logger.info(f"   {prop}: Unable to retrieve")
        
        # Get process information if running
        try:
            result = subprocess.run(['pgrep', '-f', 'nesop-store'], capture_output=True, text=True)
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                logger.info(f"   Running PIDs: {', '.join(pids)}")
                
                # Get detailed process info for first PID
                if pids and pids[0]:
                    pid = pids[0]
                    try:
                        result = subprocess.run(['ps', '-o', 'user,group,pid,ppid,cmd', '-p', pid], 
                                              capture_output=True, text=True)
                        if result.returncode == 0:
                            lines = result.stdout.strip().split('\n')
                            if len(lines) > 1:
                                logger.info(f"   Process Info: {lines[1]}")
                    except Exception:
                        pass
            else:
                logger.info("   Running PIDs: None (service not running)")
        except Exception as e:
            logger.warning(f"   Could not get process info: {e}")
    
    except Exception as e:
        logger.error(f"   Error getting service info: {e}")
    
    logger.info("")
    
    # Directory and file permissions analysis
    logger.info("4. DIRECTORY AND FILE PERMISSIONS:")
    
    app_root = Path("/opt/nesop-store")
    assets_dir = app_root / "assets"
    images_dir = assets_dir / "images"
    
    paths_to_check = [
        ("App Root", app_root),
        ("Assets Dir", assets_dir),
        ("Images Dir", images_dir)
    ]
    
    for name, path in paths_to_check:
        if path.exists():
            try:
                stat_info = path.stat()
                owner_uid = stat_info.st_uid
                owner_gid = stat_info.st_gid
                permissions = oct(stat_info.st_mode)[-3:]
                
                try:
                    owner_name = pwd.getpwuid(owner_uid).pw_name
                except KeyError:
                    owner_name = str(owner_uid)
                
                try:
                    group_name = grp.getgrgid(owner_gid).gr_name
                except KeyError:
                    group_name = str(owner_gid)
                
                logger.info(f"   {name}:")
                logger.info(f"     Path: {path}")
                logger.info(f"     Owner: {owner_name}:{group_name} ({owner_uid}:{owner_gid})")
                logger.info(f"     Permissions: {permissions}")
                
                # Check access for different users
                service_user = service_info.get('user', 'nesop')
                if service_user and service_user != 'NOT SET':
                    try:
                        service_uid = pwd.getpwnam(service_user).pw_uid
                        
                        # Check if service user can write (simplified check)
                        if owner_uid == service_uid:
                            can_write = permissions[0] in ['2', '3', '6', '7']
                            logger.info(f"     Service user ({service_user}) can write: {'Yes' if can_write else 'No'} (owner)")
                        else:
                            # Check group permissions
                            try:
                                service_user_groups = [g.gr_gid for g in grp.getgrall() if service_user in g.gr_mem]
                                service_primary_gid = pwd.getpwnam(service_user).pw_gid
                                service_user_groups.append(service_primary_gid)
                                
                                if owner_gid in service_user_groups:
                                    can_write = permissions[1] in ['2', '3', '6', '7']
                                    logger.info(f"     Service user ({service_user}) can write: {'Yes' if can_write else 'No'} (group member)")
                                else:
                                    can_write = permissions[2] in ['2', '3', '6', '7']
                                    logger.info(f"     Service user ({service_user}) can write: {'Yes' if can_write else 'No'} (other)")
                            except Exception:
                                logger.info(f"     Service user ({service_user}) can write: Unknown")
                    except KeyError:
                        logger.info(f"     Service user ({service_user}): Does not exist")
                
            except Exception as e:
                logger.error(f"   Error checking {name}: {e}")
        else:
            logger.error(f"   {name}: Does not exist - {path}")
    
    logger.info("")
    
    # Test file creation as service user
    logger.info("5. SERVICE USER WRITE TEST:")
    
    service_user = service_info.get('user', 'nesop')
    if service_user and service_user != 'NOT SET' and current_uid == 0:  # Only if running as root
        try:
            test_file = images_dir / "service_user_test.tmp"
            
            # Try to create file as service user
            cmd = ['sudo', '-u', service_user, 'touch', str(test_file)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"   ✓ Service user ({service_user}) can create files in images directory")
                # Clean up
                try:
                    test_file.unlink()
                except:
                    pass
            else:
                logger.error(f"   ✗ Service user ({service_user}) cannot create files in images directory")
                logger.error(f"   Error: {result.stderr}")
        except Exception as e:
            logger.error(f"   ✗ Could not test service user write access: {e}")
    else:
        logger.info("   Skipped (not running as root or service user not identified)")
    
    logger.info("")
    
    # Recommendations
    logger.info("6. RECOMMENDATIONS:")
    
    service_user = service_info.get('user', 'nesop')
    if service_user and service_user != 'NOT SET':
        logger.info(f"   Based on analysis, your service runs as user: {service_user}")
        logger.info("   ")
        logger.info("   IMMEDIATE FIXES TO TRY:")
        logger.info(f"   1. Fix ownership for service user:")
        logger.info(f"      sudo chown -R {service_user}:www-data /opt/nesop-store/assets/")
        logger.info("      sudo chmod -R 775 /opt/nesop-store/assets/")
        logger.info("      sudo systemctl restart nesop-store")
        logger.info("   ")
        logger.info("   2. Alternative - Add service user to www-data group:")
        logger.info(f"      sudo usermod -a -G www-data {service_user}")
        logger.info("      sudo systemctl restart nesop-store")
        logger.info("   ")
        logger.info("   3. If all else fails - Make directory world-writable (TEMPORARY):")
        logger.info("      sudo chmod 777 /opt/nesop-store/assets/images/")
        logger.info("      (Test upload, then fix properly)")
    else:
        logger.info("   Could not determine service user. Manual investigation needed.")
        logger.info("   Check the service file: /etc/systemd/system/nesop-store.service")

def main():
    """Main function"""
    diagnose_service_user()

if __name__ == "__main__":
    main() 