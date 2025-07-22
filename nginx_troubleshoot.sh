#!/bin/bash
# NESOP Store Nginx Troubleshooting Script

echo "=== NESOP Store Nginx Troubleshooting ==="
echo "Date: $(date)"
echo

echo "1. Checking nginx service status..."
sudo systemctl status nginx --no-pager -l
echo

echo "2. Checking NESOP Store service status..."
sudo systemctl status nesop-store --no-pager -l
echo

echo "3. Checking what's listening on port 80..."
sudo netstat -tlnp | grep :80
echo

echo "4. Checking what's listening on port 8080..."
sudo netstat -tlnp | grep :8080
echo

echo "5. Checking nginx configuration test..."
sudo nginx -t
echo

echo "6. Checking enabled sites..."
ls -la /etc/nginx/sites-enabled/
echo

echo "7. Checking if nesop-store config is linked..."
ls -la /etc/nginx/sites-enabled/nesop-store
echo

echo "8. Checking default nginx site..."
ls -la /etc/nginx/sites-enabled/default
echo

echo "9. Testing local connectivity to Flask app..."
curl -I http://127.0.0.1:8080/ 2>/dev/null || echo "Cannot connect to Flask app on port 8080"
echo

echo "10. Testing nginx proxy (should show Flask app)..."
curl -I http://127.0.0.1:80/ 2>/dev/null || echo "Cannot connect via nginx on port 80"
echo

echo "11. Checking nginx access logs..."
sudo tail -5 /var/log/nginx/nesop-store.access.log 2>/dev/null || echo "No nesop-store access log found"
echo

echo "12. Checking nginx error logs..."
sudo tail -5 /var/log/nginx/nesop-store.error.log 2>/dev/null || echo "No nesop-store error log found"
echo

echo "13. Checking server name in nginx config..."
grep "server_name" /etc/nginx/sites-enabled/nesop-store 2>/dev/null || echo "Cannot read nesop-store config"
echo

echo "14. Checking if accessing by IP vs domain..."
echo "Your server IP addresses:"
ip addr show | grep "inet " | grep -v "127.0.0.1"
echo

echo "=== Troubleshooting Complete ==="
echo "Please share this output to help diagnose the issue." 