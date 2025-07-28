#!/bin/bash

# NESOP Store SSL Certificate Installation Script
# This script installs the certificate received from your CA and configures Nginx

set -e

# File paths
PRIVATE_KEY="ssl/nesop-store.key"
FULL_CHAIN="ssl/nesop-store-full-chain.crt"
NGINX_CONFIG="/etc/nginx/sites-available/nesop-store"
NGINX_SSL_CONFIG="/etc/nginx/sites-available/nesop-store-ssl"

echo "=============================================="
echo "NESOP Store SSL Certificate Installation"
echo "=============================================="

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo "This script must be run as root (use sudo)"
   exit 1
fi

# Check if certificate files exist
if [[ ! -f "$PRIVATE_KEY" ]]; then
    echo "❌ Private key not found: $PRIVATE_KEY"
    exit 1
fi

if [[ ! -f "$FULL_CHAIN" ]]; then
    echo "❌ Certificate not found: $FULL_CHAIN"
    echo "Please run ./convert_certificates.sh first"
    exit 1
fi

echo "✓ Private key found: $PRIVATE_KEY"
echo "✓ Certificate found: $FULL_CHAIN"

# Verify certificate and key match
echo "Verifying certificate and private key match..."
cert_hash=$(openssl x509 -noout -modulus -in "$FULL_CHAIN" | openssl md5)
key_hash=$(openssl rsa -noout -modulus -in "$PRIVATE_KEY" | openssl md5)

if [[ "$cert_hash" == "$key_hash" ]]; then
    echo "✓ Certificate and private key match"
else
    echo "❌ Certificate and private key do not match!"
    exit 1
fi

# Copy certificates to system location
echo "Installing certificates..."
mkdir -p /etc/ssl/nesop-store
cp "$PRIVATE_KEY" /etc/ssl/nesop-store/
cp "$FULL_CHAIN" /etc/ssl/nesop-store/nesop-store.crt
chmod 600 /etc/ssl/nesop-store/nesop-store.key
chmod 644 /etc/ssl/nesop-store/nesop-store.crt
chown root:root /etc/ssl/nesop-store/*

echo "✓ Certificates installed to /etc/ssl/nesop-store/"

# Get the actual domain from the certificate
DOMAIN=$(openssl x509 -in "$FULL_CHAIN" -noout -text | grep -A1 "Subject:" | grep "CN=" | sed 's/.*CN=\([^,]*\).*/\1/' | tr -d ' ')
if [[ -z "$DOMAIN" ]]; then
    DOMAIN="store.archnexus.com"
    echo "⚠ Could not extract domain from certificate, using placeholder"
fi

echo "✓ Detected domain: $DOMAIN"

# Create SSL-enabled Nginx configuration
echo "Creating SSL-enabled Nginx configuration..."
cat > "$NGINX_SSL_CONFIG" << EOF
# HTTP server - redirect to HTTPS
server {
    listen 80;
    server_name $DOMAIN;
    
    # Redirect all HTTP requests to HTTPS
    return 301 https://\$server_name\$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name $DOMAIN;
    
    # SSL Configuration
    ssl_certificate /etc/ssl/nesop-store/nesop-store.crt;
    ssl_certificate_key /etc/ssl/nesop-store/nesop-store.key;
    
    # SSL Settings (Modern configuration)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # SSL Session Cache
    ssl_session_cache shared:SSL:1m;
    ssl_session_timeout 10m;
    
    # HSTS (HTTP Strict Transport Security)
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Proxy configuration for Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_redirect off;
        
        # Increase timeout for AD operations
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Static files
    location /assets/ {
        alias /opt/nesop-store/assets/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    location /static/ {
        alias /opt/nesop-store/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # File upload size limit
    client_max_body_size 20M;
    
    # Logging
    access_log /var/log/nginx/nesop-store-ssl.access.log;
    error_log /var/log/nginx/nesop-store-ssl.error.log;
}
EOF

echo "✓ SSL Nginx configuration created: $NGINX_SSL_CONFIG"

# Enable SSL configuration
echo "Enabling SSL configuration..."
ln -sf "$NGINX_SSL_CONFIG" /etc/nginx/sites-enabled/nesop-store

# Test Nginx configuration
echo "Testing Nginx configuration..."
nginx -t

if [[ $? -eq 0 ]]; then
    echo "✓ Nginx configuration is valid"
    
    # Reload Nginx
    echo "Reloading Nginx..."
    systemctl reload nginx
    echo "✓ Nginx reloaded successfully"
    
    echo ""
    echo "=============================================="
    echo "SSL Certificate Installation Complete!"
    echo "=============================================="
    echo "Your NESOP Store is now accessible via HTTPS"
    echo "URL: https://$DOMAIN"
    echo ""
    echo "Certificate details:"
    openssl x509 -in "$FULL_CHAIN" -text -noout | grep -A 2 "Subject:"
    openssl x509 -in "$FULL_CHAIN" -text -noout | grep -A 2 "Not Before\|Not After"
    
else
    echo "❌ Nginx configuration test failed"
    echo "Please check the configuration and try again"
    exit 1
fi
