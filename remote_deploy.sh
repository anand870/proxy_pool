#!/usr/bin/env bash
# ==============================================================================
# Remote Deployment Script for GCP Compute Engine e2-micro VM Instance
# Run this script locally to deploy proxy_pool onto a running GCP e2-micro VM.
# ==============================================================================
set -e

# Configuration (Can be passed via arguments or environment variables)
INSTANCE_NAME="${1:-${INSTANCE_NAME:-my-gcp-micro-instance}}"
ZONE="${2:-${ZONE:-us-central1-a}}"
GIT_REPO_URL="${3:-${GIT_REPO_URL:-https://github.com/anand870/proxy_pool.git}}"
TARGET_DIR="${TARGET_DIR:-/opt/proxy_pool}"
AUTH_TOKEN="${AUTH_TOKEN:-}"
PORT="${PORT:-5010}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

log_info "================================================================="
log_info " Deploying ProxyPool to Remote GCP Compute Engine Instance"
log_info " Instance Name: ${INSTANCE_NAME}"
log_info " Zone:          ${ZONE}"
log_info " Git Repo:      ${GIT_REPO_URL}"
log_info " Target Dir:    ${TARGET_DIR}"
log_info " Port:          ${PORT}"
log_info "================================================================="

# Check gcloud CLI
if ! command -v gcloud &>/dev/null; then
    log_error "'gcloud' CLI tool is required to SSH into Google Cloud instances."
    log_error "Please install Google Cloud SDK: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

log_info "[1/5] Opening GCP Firewall port ${PORT} to public ingress..."
# Create firewall rule allowing port 5010 for instances tagged with proxy-pool
gcloud compute firewall-rules create "allow-proxy-pool-${PORT}" \
    --allow="tcp:${PORT}" \
    --source-ranges="0.0.0.0/0" \
    --target-tags="proxy-pool" \
    --description="Allow public ingress traffic on port ${PORT} for ProxyPool" &>/dev/null || log_warn "Firewall rule 'allow-proxy-pool-${PORT}' already exists or updated."


# Add network tag proxy-pool to the VM instance
gcloud compute instances add-tags "${INSTANCE_NAME}" \
    --zone="${ZONE}" \
    --tags="proxy-pool" &>/dev/null || log_warn "Network tag 'proxy-pool' already present on ${INSTANCE_NAME}."

log_info "[2/5] Installing git, python3, venv, and redis on remote GCP VM..."
gcloud compute ssh "${INSTANCE_NAME}" --zone="${ZONE}" --command="
    sudo apt-get update -y && \
    sudo apt-get install -y git python3 python3-venv redis-server curl
"

log_info "[3/5] Cloning or pulling project repository on remote GCP VM..."
gcloud compute ssh "${INSTANCE_NAME}" --zone="${ZONE}" --command="
    sudo mkdir -p ${TARGET_DIR} && \
    sudo chown -R \$USER:\$USER ${TARGET_DIR} && \
    if [ -d '${TARGET_DIR}/.git' ]; then
        echo 'Updating existing repository...' && \
        cd ${TARGET_DIR} && git fetch --all && (git reset --hard origin/master || git pull)
    else
        echo 'Cloning repository...' && \
        git clone ${GIT_REPO_URL} ${TARGET_DIR}
    fi
"

log_info "[4/5] Running deploy.sh on remote GCP VM..."
gcloud compute ssh "${INSTANCE_NAME}" --zone="${ZONE}" --command="
    cd ${TARGET_DIR} && \
    chmod +x deploy.sh proxy_pool.sh && \
    ./deploy.sh
"

if [ -n "${AUTH_TOKEN}" ]; then
    log_info "Setting AUTH_TOKEN in remote .env configuration..."
    gcloud compute ssh "${INSTANCE_NAME}" --zone="${ZONE}" --command="
        sed -i 's/^AUTH_TOKEN=.*/AUTH_TOKEN=${AUTH_TOKEN}/' ${TARGET_DIR}/.env
    "
fi

log_info "[5/5] Starting ProxyPool production service on remote GCP VM..."
gcloud compute ssh "${INSTANCE_NAME}" --zone="${ZONE}" --command="
    if command -v systemctl &>/dev/null && [ -f /etc/systemd/system/proxy_pool.service ]; then
        sudo systemctl restart proxy_pool && \
        sudo systemctl status proxy_pool --no-pager
    else
        cd ${TARGET_DIR} && ./proxy_pool.sh restart
    fi
"

EXTERNAL_IP=$(gcloud compute instances describe "${INSTANCE_NAME}" --zone="${ZONE}" --format='get(networkInterfaces[0].accessConfigs[0].natIP)' 2>/dev/null || echo "<INSTANCE_EXTERNAL_IP>")

log_info ""
log_info "================================================================="
log_info " Remote Deployment Completed Successfully!"
log_info " ProxyPool Public URL: http://${EXTERNAL_IP}:${PORT}"
if [ -n "${AUTH_TOKEN}" ]; then
    log_info " Token Auth Enabled: Header 'Authorization: Bearer ${AUTH_TOKEN}' or '?token=${AUTH_TOKEN}'"
else
    log_info " Token Auth: Disabled (Pass AUTH_TOKEN='your_token' to enable)"
fi
log_info "================================================================="
