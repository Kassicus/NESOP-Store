#!/bin/bash

# NESOP Store SSL Certificate Request Generator
# This script generates a private key and Certificate Signing Request (CSR) for your internal CA

set -e

# Configuration - UPDATE THESE VALUES FOR YOUR ENVIRONMENT
DOMAIN="store.archnexus.com"  # Replace with your actual domain
ORG="Architectural Nexus"
OU="IT"
CITY="Salt Lake City"        # Replace with your city
STATE="UT"      # Replace with your state
COUNTRY="US"           # Replace with your country code
EMAIL="helpdesk@archnexus.com"  # Replace with your admin email

# Certificate files
PRIVATE_KEY="ssl/nesop-store.key"
CSR_FILE="ssl/nesop-store.csr"
CONFIG_FILE="ssl/nesop-store.conf"

echo "=============================================="
echo "NESOP Store SSL Certificate Request Generator"
echo "=============================================="

# Create ssl directory if it doesn't exist
mkdir -p ssl

# Create OpenSSL configuration file
echo "Creating OpenSSL configuration..."
cat > "$CONFIG_FILE" << EOF
[req]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no

[req_distinguished_name]
C=$COUNTRY
ST=$STATE
L=$CITY
O=$ORG
OU=$OU
CN=$DOMAIN
emailAddress=$EMAIL

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = $DOMAIN
DNS.2 = store
IP.1 = 10.1.6.28
EOF

echo "✓ Configuration file created: $CONFIG_FILE"

# Generate private key (2048-bit RSA)
echo "Generating private key..."
openssl genrsa -out "$PRIVATE_KEY" 2048
chmod 600 "$PRIVATE_KEY"
echo "✓ Private key generated: $PRIVATE_KEY"

# Generate Certificate Signing Request (PKCS#10 format)
echo "Generating Certificate Signing Request (CSR)..."
openssl req -new -key "$PRIVATE_KEY" -out "$CSR_FILE" -config "$CONFIG_FILE"
echo "✓ CSR generated: $CSR_FILE"

# Display CSR information
echo ""
echo "=============================================="
echo "Certificate Signing Request (CSR) Details"
echo "=============================================="
openssl req -in "$CSR_FILE" -text -noout

echo ""
echo "=============================================="
echo "CSR Generation Complete!"
echo "=============================================="
echo "Files created:"
echo "  Private Key: $PRIVATE_KEY (Keep this secure!)"
echo "  CSR File:    $CSR_FILE (Submit this to your CA)"
echo "  Config File: $CONFIG_FILE"
echo ""
echo "Next steps:"
echo "1. Submit $CSR_FILE to your internal CA"
echo "2. Once you receive the certificate, save it as ssl/nesop-store.crt"
echo "3. If you receive a CA chain, save it as ssl/ca-chain.crt"
echo "4. Run the install_certificate.sh script to configure SSL"
echo ""
echo "CSR Content (copy this to your CA if needed):"
echo "=============================================="
cat "$CSR_FILE"
echo "=============================================="
