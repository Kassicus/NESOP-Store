#!/bin/bash

# NESOP Store Certificate Conversion Script
# Converts CA-provided certificates to PEM format for Nginx

set -e

# Input files from CA
CER_FILE="ssl/nesop-store.cer"
P7B_FILE="ssl/nesop-store.p7b"

# Output files for Nginx
CERT_PEM="ssl/nesop-store.crt"
CHAIN_PEM="ssl/ca-chain.crt"
FULL_CHAIN="ssl/nesop-store-full-chain.crt"

echo "=============================================="
echo "NESOP Store Certificate Conversion"
echo "=============================================="

# Check if input files exist
if [[ ! -f "$CER_FILE" ]]; then
    echo "❌ Certificate file not found: $CER_FILE"
    echo "Please save your certificate as $CER_FILE"
    exit 1
fi

if [[ ! -f "$P7B_FILE" ]]; then
    echo "❌ PKCS#7 file not found: $P7B_FILE"
    echo "Please save your PKCS#7 file as $P7B_FILE"
    exit 1
fi

echo "✓ Found certificate file: $CER_FILE"
echo "✓ Found PKCS#7 file: $P7B_FILE"

# Convert .cer to PEM format (handles both DER and PEM input)
echo "Converting certificate to PEM format..."
if openssl x509 -in "$CER_FILE" -inform DER -out "$CERT_PEM" 2>/dev/null; then
    echo "✓ Converted DER certificate to PEM: $CERT_PEM"
elif openssl x509 -in "$CER_FILE" -inform PEM -out "$CERT_PEM" 2>/dev/null; then
    echo "✓ Certificate was already in PEM format: $CERT_PEM"
else
    echo "❌ Failed to convert certificate"
    exit 1
fi

# Extract certificates from PKCS#7 file
echo "Extracting certificates from PKCS#7 file..."
openssl pkcs7 -inform DER -in "$P7B_FILE" -print_certs -out temp_certs.pem 2>/dev/null || \
openssl pkcs7 -inform PEM -in "$P7B_FILE" -print_certs -out temp_certs.pem

if [[ $? -eq 0 ]]; then
    echo "✓ Extracted certificates from PKCS#7 file"
else
    echo "❌ Failed to extract certificates from PKCS#7 file"
    exit 1
fi

# Split the certificates
echo "Processing certificate chain..."
awk 'BEGIN {c=0;} /-----BEGIN CERT/{c++} { print > "ssl/cert" c ".pem"}' temp_certs.pem

# Find your server certificate and CA certificates
cert_count=$(ls ssl/cert*.pem | wc -l)
echo "✓ Found $cert_count certificates in the chain"

# Identify server certificate vs CA certificates
server_cert=""
ca_certs=""

for cert_file in ssl/cert*.pem; do
    if [[ -f "$cert_file" ]]; then
        # Check if this certificate matches our domain
        if openssl x509 -in "$cert_file" -noout -text | grep -q "$(openssl x509 -in "$CERT_PEM" -noout -subject)"; then
            server_cert="$cert_file"
            echo "✓ Identified server certificate: $cert_file"
        else
            ca_certs="$ca_certs $cert_file"
            echo "✓ Identified CA certificate: $cert_file"
        fi
    fi
done

# Create CA chain file (intermediate + root CAs)
if [[ -n "$ca_certs" ]]; then
    cat $ca_certs > "$CHAIN_PEM"
    echo "✓ Created CA chain file: $CHAIN_PEM"
    
    # Create full chain (server cert + CA chain)
    cat "$CERT_PEM" "$CHAIN_PEM" > "$FULL_CHAIN"
    echo "✓ Created full chain certificate: $FULL_CHAIN"
else
    echo "⚠ No CA certificates found, using server certificate only"
    cp "$CERT_PEM" "$FULL_CHAIN"
fi

# Clean up temporary files
rm -f temp_certs.pem ssl/cert*.pem

# Verify the certificate
echo "Verifying certificate..."
if openssl x509 -in "$CERT_PEM" -noout -text > /dev/null; then
    echo "✓ Certificate is valid"
    
    # Show certificate details
    echo ""
    echo "Certificate Details:"
    echo "==================="
    openssl x509 -in "$CERT_PEM" -noout -subject -issuer -dates
    
    # Check certificate and key match
    if [[ -f "ssl/nesop-store.key" ]]; then
        cert_hash=$(openssl x509 -noout -modulus -in "$CERT_PEM" | openssl md5)
        key_hash=$(openssl rsa -noout -modulus -in "ssl/nesop-store.key" | openssl md5)
        
        if [[ "$cert_hash" == "$key_hash" ]]; then
            echo "✓ Certificate matches private key"
        else
            echo "❌ Certificate does NOT match private key!"
            exit 1
        fi
    fi
else
    echo "❌ Certificate validation failed"
    exit 1
fi

echo ""
echo "=============================================="
echo "Certificate Conversion Complete!"
echo "=============================================="
echo "Files ready for installation:"
echo "  Server Certificate: $CERT_PEM"
echo "  CA Chain: $CHAIN_PEM"
echo "  Full Chain: $FULL_CHAIN"
echo "  Private Key: ssl/nesop-store.key"
echo ""
echo "Next step: Run ./install_certificate.sh to configure SSL"
