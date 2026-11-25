#!/usr/bin/env bash
# ==============================================================================
# StenoVision - Idempotent HTTPS/TLS Provisioning Script (Port 443)
# Configures SAN self-signed fallback for raw IP AND trusted Let's Encrypt
# certificate for <IP-DASHED>.sslip.io via ACME HTTP-01 challenge.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
SSL_DIR="$REPO_DIR/deploy/nginx/ssl"
CERTBOT_WEBROOT="$REPO_DIR/deploy/nginx/certbot"

PUBLIC_IP="${1:-56.228.24.218}"
DOMAIN="${2:-${PUBLIC_IP//./-}.sslip.io}"

echo "[+] Provisioning HTTPS certificates for IP=${PUBLIC_IP}, Domain=${DOMAIN}"
mkdir -p "$SSL_DIR" "$CERTBOT_WEBROOT"

# 1. Generate SAN self-signed certificate for raw IP fallback (always needed so Nginx starts cleanly)
if [ ! -f "$SSL_DIR/selfsigned.crt" ] || [ ! -f "$SSL_DIR/selfsigned.key" ]; then
  echo "[+] Generating 2048-bit OpenSSL SAN certificate for IP:${PUBLIC_IP} and DNS:${DOMAIN}..."
  openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
    -keyout "$SSL_DIR/selfsigned.key" \
    -out "$SSL_DIR/selfsigned.crt" \
    -subj "/CN=${DOMAIN}" \
    -addext "subjectAltName = IP:${PUBLIC_IP},DNS:${DOMAIN}"
  chmod 600 "$SSL_DIR/selfsigned.key"
  chmod 644 "$SSL_DIR/selfsigned.crt"
fi

# 2. Seed sslip.{crt,key} with self-signed cert initially if not yet issued by Let's Encrypt
if [ ! -f "$SSL_DIR/sslip.crt" ] || [ ! -f "$SSL_DIR/sslip.key" ]; then
  cp "$SSL_DIR/selfsigned.crt" "$SSL_DIR/sslip.crt"
  cp "$SSL_DIR/selfsigned.key" "$SSL_DIR/sslip.key"
fi

# 3. Ensure Nginx container is up with port 80 & 443 mapped so HTTP-01 challenge works
cd "$REPO_DIR"
docker compose up -d --force-recreate nginx

# 4. Install Certbot if missing and attempt trusted Let's Encrypt issuance
if ! command -v certbot &> /dev/null; then
  echo "[+] Installing Certbot..."
  export DEBIAN_FRONTEND=noninteractive
  apt-get update -y
  apt-get install -y --no-install-recommends certbot
fi

echo "[+] Requesting Let's Encrypt certificate for ${DOMAIN}..."
if certbot certonly --webroot \
  -w "$CERTBOT_WEBROOT" \
  -d "$DOMAIN" \
  --non-interactive \
  --agree-tos \
  --register-unsafely-without-email \
  --keep-until-expiring; then

  LE_LIVE="/etc/letsencrypt/live/${DOMAIN}"
  if [ -f "${LE_LIVE}/fullchain.pem" ] && [ -f "${LE_LIVE}/privkey.pem" ]; then
    cp -L "${LE_LIVE}/fullchain.pem" "$SSL_DIR/sslip.crt"
    cp -L "${LE_LIVE}/privkey.pem" "$SSL_DIR/sslip.key"
    chmod 644 "$SSL_DIR/sslip.crt"
    chmod 600 "$SSL_DIR/sslip.key"

    # Install renewal deploy hook to copy renewed certs & reload Nginx
    mkdir -p /etc/letsencrypt/renewal-hooks/deploy
    cat << HOOK > /etc/letsencrypt/renewal-hooks/deploy/stenovision_nginx_reload.sh
#!/usr/bin/env bash
if [ -f "${LE_LIVE}/fullchain.pem" ] && [ -f "${LE_LIVE}/privkey.pem" ]; then
  cp -L "${LE_LIVE}/fullchain.pem" "${SSL_DIR}/sslip.crt"
  cp -L "${LE_LIVE}/privkey.pem" "${SSL_DIR}/sslip.key"
  docker exec stenovision_nginx nginx -s reload || true
fi
HOOK
    chmod +x /etc/letsencrypt/renewal-hooks/deploy/stenovision_nginx_reload.sh

    docker exec stenovision_nginx nginx -t
    docker exec stenovision_nginx nginx -s reload
    echo "[+] Trusted Let's Encrypt HTTPS active at: https://${DOMAIN}/"
  fi
else
  echo "[!] Warning: Let's Encrypt issuance failed (check port 80 reachability or rate limits). Self-signed HTTPS fallback remains active on port 443."
  docker exec stenovision_nginx nginx -t
  docker exec stenovision_nginx nginx -s reload
fi
