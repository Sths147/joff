#!/bin/sh
# Runs automatically before nginx starts (official nginx image convention:
# every executable script in /docker-entrypoint.d/ is sourced on boot).
#
# Generates a self-signed cert on first start if one isn't already sitting in
# the mounted nginx_certs volume (see docker-compose.yml) — no domain exists
# yet, so there's nothing for Let's Encrypt/a real CA to issue against.
# Swapping in a real cert later, once a domain is pointed at this server, is a
# manual file replacement in that volume, not automatic.
set -e

CERT_DIR=/etc/nginx/certs
CERT="$CERT_DIR/selfsigned.crt"
KEY="$CERT_DIR/selfsigned.key"

if [ ! -f "$CERT" ] || [ ! -f "$KEY" ]; then
    mkdir -p "$CERT_DIR"
    openssl req -x509 -nodes -newkey rsa:2048 \
        -keyout "$KEY" -out "$CERT" \
        -days 365 -subj "/CN=localhost"
fi
