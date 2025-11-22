#!/bin/bash
# Server setup script - run once to initialize the server
set -e

DOMAIN="${DOMAIN:-pump-researcher.aizenshtat.eu}"
EMAIL="${CERTBOT_EMAIL:-admin@aizenshtat.eu}"

echo "=== Setting up server for $DOMAIN ==="

# Install dependencies
echo "Installing dependencies..."
apt-get update
apt-get install -y docker.io docker-compose nginx certbot python3-certbot-nginx

# Enable and start Docker
systemctl enable docker
systemctl start docker

# Create directories
mkdir -p /var/www/certbot
mkdir -p /opt/pump-researcher/data

# Copy nginx config (without SSL first for certbot)
cat > /etc/nginx/sites-available/pump-researcher << EOF
server {
    listen 80;
    server_name $DOMAIN;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/pump-researcher /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test and reload nginx
nginx -t
systemctl reload nginx

# Get SSL certificate
echo "Obtaining SSL certificate..."
certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

# Setup auto-renewal
echo "0 12 * * * root certbot renew --quiet" > /etc/cron.d/certbot-renew

echo "=== Server setup complete ==="
echo "SSL certificate installed for $DOMAIN"
