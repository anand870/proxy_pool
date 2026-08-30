#!/usr/bin/env bash
# ==============================================================================
# ProxyPool Host Machine Production Deployment Script
# Optimized for Google Cloud Compute Engine e2-micro Always Free Tier
# ==============================================================================
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

log_info "Starting ProxyPool Host Deployment Setup for GCP e2-micro..."

# 1. Check Python installation
PYTHON_CMD=""
if command -v python3 &>/dev/null; then
    PYTHON_CMD="python3"
elif command -v python &>/dev/null; then
    PYTHON_CMD="python"
else
    log_error "Python 3 is required but not installed."
    exit 1
fi

PY_VER=$($PYTHON_CMD -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
log_info "Detected Python version: $PY_VER ($PYTHON_CMD)"

# 2. Setup Virtual Environment
VENV_DIR="$SCRIPT_DIR/venv"
if [ ! -d "$VENV_DIR" ]; then
    log_info "Creating virtual environment in $VENV_DIR..."
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

VENV_PYTHON="$VENV_DIR/bin/python"
VENV_PIP="$VENV_DIR/bin/pip"

log_info "Upgrading pip and installing requirements..."
$VENV_PIP install --upgrade pip -q
$VENV_PIP install -r requirements.txt -q

# 3. Setup Default .env Configuration
ENV_FILE="$SCRIPT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    log_info "Creating default .env configuration file..."
    cat <<EOF > "$ENV_FILE"
# Server Configuration
HOST=0.0.0.0
PORT=5010

# API Token Authentication (Set non-empty token string to enable protection)
AUTH_TOKEN=

# Database Connection (Default local Redis)
DB_CONN=redis://@127.0.0.1:6379/0

# Production Gunicorn Performance Tuning for GCP e2-micro Free Tier (1GB RAM)
GUNICORN_WORKERS=2
GUNICORN_THREADS=2
LOG_LEVEL=INFO

# Proxy Fetching & Validation
POOL_SIZE_MIN=20
VERIFY_TIMEOUT=10
MAX_FAIL_COUNT=0
TIMEZONE=Asia/Shanghai
EOF
    log_info "Generated default .env configuration at $ENV_FILE"
fi

# 4. Check Redis Service
if command -v redis-cli &>/dev/null; then
    if redis-cli ping &>/dev/null; then
        log_info "Local Redis server is running."
    else
        log_warn "Local Redis server is installed but not currently responding to ping."
    fi
else
    log_warn "redis-cli not found in PATH. Ensure Redis server is reachable via DB_CONN in .env"
fi

# 5. Setup Systemd Service (if sudo/systemd available)
SERVICE_DEST="/etc/systemd/system/proxy_pool.service"
if [ -d "/etc/systemd/system" ] && command -v systemctl &>/dev/null; then
    if [ "$EUID" -eq 0 ] || command -v sudo &>/dev/null; then
        log_info "Configuring systemd service proxy_pool.service..."
        
        # Prepare service file with actual path
        TEMP_SERVICE=$(mktemp)
        cat <<EOF > "$TEMP_SERVICE"
[Unit]
Description=ProxyPool Production Service (GCP Compute Engine e2-micro Free Tier)
After=network.target redis-server.service redis.service

[Service]
Type=simple
WorkingDirectory=$SCRIPT_DIR
Environment="PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin"
EnvironmentFile=-$SCRIPT_DIR/.env
ExecStart=$SCRIPT_DIR/proxy_pool.sh start --fg
ExecStop=$SCRIPT_DIR/proxy_pool.sh stop
Restart=always
RestartSec=5
LimitNOFILE=65536
MemoryMax=350M

[Install]
WantedBy=multi-user.target
EOF
        if [ "$EUID" -eq 0 ]; then
            cp "$TEMP_SERVICE" "$SERVICE_DEST"
            systemctl daemon-reload
        else
            sudo cp "$TEMP_SERVICE" "$SERVICE_DEST"
            sudo systemctl daemon-reload
        fi
        rm -f "$TEMP_SERVICE"
        log_info "Installed systemd service to $SERVICE_DEST"
        log_info "To start service via systemd: sudo systemctl start proxy_pool"
        log_info "To enable auto-start on boot: sudo systemctl enable proxy_pool"
    fi
fi

log_info "Deployment setup complete for GCP Compute Engine e2-micro!"
log_info ""
log_info "Usage:"
log_info "  Start in background: ./proxy_pool.sh start"
log_info "  Check status:       ./proxy_pool.sh status"
log_info "  Stop service:       ./proxy_pool.sh stop"
log_info "  Systemd start:      sudo systemctl start proxy_pool"
EOF
