#!/bin/sh
set -eu

CERT_DIR="/etc/letsencrypt/live/app.occacia.com"
HTTP_CONF="/etc/nginx/templates/nginx.http.conf"
HTTPS_CONF="/etc/nginx/templates/nginx.https.conf"
TARGET_CONF="/etc/nginx/nginx.conf"

if [ -f "$CERT_DIR/fullchain.pem" ] && [ -f "$CERT_DIR/privkey.pem" ]; then
    echo "Using HTTPS Nginx configuration."
    cp "$HTTPS_CONF" "$TARGET_CONF"
else
    echo "LetsEncrypt certificates not found. Falling back to HTTP-only Nginx configuration."
    cp "$HTTP_CONF" "$TARGET_CONF"
fi

exec nginx -g 'daemon off;'
