#!/bin/bash
# NESOP Store - Complete Uninstall Script
# This script removes all traces of the NESOP Store application from the server

set -e

echo "======================================================="
echo "NESOP Store - Complete Uninstall Script"
echo "======================================================="
echo "This script will completely remove NESOP Store from your server"
echo "including:"
echo "  - Systemd service"
echo "  - Application files (/opt/nesop-store)"
echo "  - Nginx configuration"
echo "  - Database files"
echo "  - System user (optional)"
echo "  - Logs and temporary files"
echo ""
read -p "Are you sure you want to proceed? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstall cancelled."
    exit 0
fi

echo "Starting NESOP Store uninstall process..."
echo ""

# Function to safely remove files/directories
safe_remove() {
    local target="$1"
    if [ -e "$target" ]; then
        echo "  Removing: $target"
        rm -rf "$target"
    else
        echo "  Not found: $target (skipping)"
    fi
}

# Function to run command with error handling
run_command() {
    local cmd="$1"
    local description="$2"
    
    echo "  $description..."
    if eval "$cmd" 2>/dev/null; then
        echo "    ✓ Success"
    else
        echo "    ⚠ Warning: Command failed (continuing anyway)"
    fi
}

# Step 1: Stop and remove systemd service
echo "1. Stopping and removing systemd service..."
run_command "sudo systemctl stop nesop-store.service" "Stopping nesop-store service"
run_command "sudo systemctl disable nesop-store.service" "Disabling nesop-store service"
safe_remove "/etc/systemd/system/nesop-store.service"
run_command "sudo systemctl daemon-reload" "Reloading systemd daemon"

# Step 2: Remove nginx configuration
echo ""
echo "2. Removing nginx configuration..."
safe_remove "/etc/nginx/sites-available/nesop-store"
safe_remove "/etc/nginx/sites-enabled/nesop-store"
run_command "sudo nginx -t" "Testing nginx configuration"
run_command "sudo systemctl restart nginx" "Restarting nginx"

# Step 3: Remove application files
echo ""
echo "3. Removing application files..."
safe_remove "/opt/nesop-store"

# Step 4: Remove temporary deployment files
echo ""
echo "4. Removing temporary deployment files..."
safe_remove "/tmp/nesop-store-deployment-*"

# Step 5: Clean up logs
echo ""
echo "5. Cleaning up logs..."
safe_remove "/var/log/nginx/nesop-store.access.log"
safe_remove "/var/log/nginx/nesop-store.error.log"
safe_remove "/var/log/nesop-store"

# Step 6: Remove database backups (optional)
echo ""
echo "6. Removing database backups..."
find /tmp -name "nesop_store*.db*" -type f -delete 2>/dev/null || true
find /opt -name "nesop_store*.db*" -type f -delete 2>/dev/null || true

# Step 7: Remove system user (optional)
echo ""
echo "7. System user removal (optional)..."
read -p "Remove the 'nesop' system user? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if id "nesop" &>/dev/null; then
        run_command "sudo userdel -r nesop" "Removing nesop user and home directory"
    else
        echo "  User 'nesop' not found (skipping)"
    fi
else
    echo "  Keeping 'nesop' user"
fi

# Step 8: Clean up Python packages (optional)
echo ""
echo "8. Python package cleanup (optional)..."
read -p "Remove Python packages that were installed for NESOP Store? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "  Note: This will remove Flask, gunicorn, and other packages"
    echo "  that might be used by other applications."
    read -p "  Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        run_command "sudo pip3 uninstall -y flask gunicorn ldap3 supervisor" "Removing Python packages"
    fi
else
    echo "  Keeping Python packages"
fi

# Step 9: Clean up any remaining processes
echo ""
echo "9. Checking for remaining processes..."
if pgrep -f "nesop-store" >/dev/null; then
    echo "  Warning: Found running NESOP Store processes"
    run_command "sudo pkill -f nesop-store" "Killing remaining processes"
else
    echo "  No remaining processes found"
fi

# Step 10: Verification
echo ""
echo "10. Verification..."
echo "  Checking for remaining files..."

remaining_files=0
check_paths=(
    "/opt/nesop-store"
    "/etc/systemd/system/nesop-store.service"
    "/etc/nginx/sites-available/nesop-store"
    "/etc/nginx/sites-enabled/nesop-store"
)

for path in "${check_paths[@]}"; do
    if [ -e "$path" ]; then
        echo "    ⚠ Still exists: $path"
        ((remaining_files++))
    else
        echo "    ✓ Removed: $path"
    fi
done

echo ""
echo "======================================================="
echo "NESOP Store Uninstall Complete!"
echo "======================================================="

if [ $remaining_files -eq 0 ]; then
    echo "✅ All components successfully removed!"
else
    echo "⚠ $remaining_files components still exist (may need manual removal)"
fi

echo ""
echo "Summary of what was removed:"
echo "  ✓ Systemd service (nesop-store.service)"
echo "  ✓ Application files (/opt/nesop-store)"
echo "  ✓ Nginx configuration"
echo "  ✓ Database files"
echo "  ✓ Temporary deployment files"
echo "  ✓ Log files"
echo ""
echo "Your server is now clean and ready for a fresh deployment!"
echo ""
echo "To redeploy NESOP Store:"
echo "  1. Copy your new deployment package to the server"
echo "  2. Extract: tar -xzf nesop-store-deployment-*.tar.gz"
echo "  3. Run: cd nesop-store-deployment-* && python3 deploy_config.py"
echo "  4. Deploy: sudo ./deploy.sh"
echo ""
echo "Have a great day! 🚀" 