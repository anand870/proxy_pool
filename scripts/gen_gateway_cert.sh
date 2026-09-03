#!/usr/bin/env bash
# ==============================================================================
# gen_gateway_cert.sh
#
# Generate a self-signed TLS leaf certificate for the ProxyPool HTTPS gateway.
#   - RSA-2048, 3650 days (~10 years)
#   - Not a CA: this is an x509 leaf cert (openssl req -x509)
#   - SAN = IP:127.0.0.1  [+ IP:<EXTERNAL_IP>]  [+ DNS:<GATEWAY_DOMAIN>]
#
# Output: <OUT_DIR>/tls.crt and <OUT_DIR>/tls.key  (OUT_DIR default: <repo>/gateway)
#
# To move to a real CA-signed cert (clients then need no --cacert):
#   1. Point a DNS name at the VM and set GATEWAY_DOMAIN in .env
#   2. Obtain a genuine cert (e.g. Let's Encrypt / certbot)
#   3. Drop the real fullchain + private key in as gateway/tls.crt / gateway/tls.key
#      and restart the service.
#
# Usage:
#   scripts/gen_gateway_cert.sh [--force]
#   GATEWAY_DOMAIN=proxy.example.com EXTERNAL_IP=203.0.113.10 scripts/gen_gateway_cert.sh
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

OUT_DIR="${OUT_DIR:-$REPO_DIR/gateway}"
GATEWAY_DOMAIN="${GATEWAY_DOMAIN:-}"
EXTERNAL_IP="${EXTERNAL_IP:-}"
FORCE="${FORCE:-}"

for arg in "$@"; do
    case "$arg" in
        --force|-f) FORCE=1 ;;
        *) echo "Unknown argument: $arg" >&2; exit 1 ;;
    esac
done

CRT="$OUT_DIR/tls.crt"
KEY="$OUT_DIR/tls.key"

mkdir -p "$OUT_DIR"

if [ -f "$CRT" ] && [ -f "$KEY" ] && [ -z "$FORCE" ]; then
    echo "[INFO] $CRT already exists; skipping (use --force to regenerate)."
    exit 0
fi

# Auto-detect the VM external IP when not supplied.
if [ -z "$EXTERNAL_IP" ]; then
    EXTERNAL_IP="$(curl -s -m 2 -H 'Metadata-Flavor: Google' \
        'http://169.254.169.254/computeMetadata/v1/instance/network-interfaces/0/access-configs/0/external-ip' 2>/dev/null || true)"
fi
if [ -z "$EXTERNAL_IP" ]; then
    EXTERNAL_IP="$(curl -s -m 3 https://ifconfig.me 2>/dev/null || true)"
fi

# Build the SAN list.
SAN="IP:127.0.0.1"
if [ -n "$EXTERNAL_IP" ]; then
    SAN="$SAN,IP:$EXTERNAL_IP"
fi
if [ -n "$GATEWAY_DOMAIN" ]; then
    SAN="$SAN,DNS:$GATEWAY_DOMAIN"
fi

CN="${GATEWAY_DOMAIN:-proxy-pool-gateway}"

echo "[INFO] Generating self-signed gateway cert"
echo "[INFO]   CN  = $CN"
echo "[INFO]   SAN = $SAN"

openssl req -x509 -newkey rsa:2048 -nodes \
    -keyout "$KEY" \
    -out "$CRT" \
    -days 3650 \
    -subj "/CN=$CN" \
    -addext "subjectAltName=$SAN"

chmod 600 "$KEY"
chmod 644 "$CRT"

echo "[INFO] Wrote $CRT"
echo "[INFO] Wrote $KEY (mode 600)"
