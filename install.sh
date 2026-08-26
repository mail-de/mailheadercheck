#!/usr/bin/env bash

set -Eeuo pipefail

INSTALL_DIR="/usr/local/sbin"
CONFIG_DIR="/etc/mailheadercheck"
CONFIG_FILE="$CONFIG_DIR/config.yaml"
SERVICE_FILE="/etc/systemd/system/mailheadercheck.service"

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"

log() {
    echo "[INFO] $*"
}

error() {
    echo "[ERROR] $*" >&2
}

die() {
    error "$*"
    exit 1
}

trap 'error "Installation failed at line $LINENO: $BASH_COMMAND"' ERR

# ---------------------------------------------------------------------------
# Root check
# ---------------------------------------------------------------------------

if [[ "${EUID}" -ne 0 ]]; then
    die "This installer must be run as root. Please run: sudo $0"
fi

# ---------------------------------------------------------------------------
# Check required files
# ---------------------------------------------------------------------------

REQUIRED_FILES=(
    "$SCRIPT_DIR/requirements.txt"
    "$SCRIPT_DIR/mailheadercheck"
    "$SCRIPT_DIR/mailheaderchecklib"
    "$SCRIPT_DIR/contrib/systemd/mailheadercheck.service"
    "$SCRIPT_DIR/examples/config.yaml"
)

log "Checking installation files..."

for file in "${REQUIRED_FILES[@]}"; do
    if [[ ! -e "$file" ]]; then
        die "Required file or directory not found: $file"
    fi
done

# ---------------------------------------------------------------------------
# Check operating system
# ---------------------------------------------------------------------------

if [[ ! -f /etc/os-release ]]; then
    die "Cannot determine operating system."
fi

# shellcheck disable=SC1091
source /etc/os-release

if [[ "${ID:-}" != "debian" && "${ID_LIKE:-}" != *debian* ]]; then
    die "This installer currently supports Debian-based systems only."
fi

# ---------------------------------------------------------------------------
# Install system dependencies
# ---------------------------------------------------------------------------

log "Updating package information..."

apt-get update

log "Installing system dependencies..."

DEBIAN_FRONTEND=noninteractive apt-get install -y \
    python3-dev \
    libmilter-dev \
    python3-pip

# ---------------------------------------------------------------------------
# Install Python dependencies
# ---------------------------------------------------------------------------

log "Installing Python dependencies..."

python3 -m pip install \
    --break-system-packages \
    --requirement "$SCRIPT_DIR/requirements.txt"

# ---------------------------------------------------------------------------
# Install application
# ---------------------------------------------------------------------------

log "Installing mailheadercheck..."

install -d -m 0755 "$INSTALL_DIR"

install -m 0755 \
    "$SCRIPT_DIR/mailheadercheck" \
    "$INSTALL_DIR/mailheadercheck"

# Replace the installed library with the current version.
rm -rf "$INSTALL_DIR/mailheaderchecklib"

cp -a \
    "$SCRIPT_DIR/mailheaderchecklib" \
    "$INSTALL_DIR/mailheaderchecklib"

chmod -R a+rX "$INSTALL_DIR/mailheaderchecklib"

# ---------------------------------------------------------------------------
# Install systemd service
# ---------------------------------------------------------------------------

log "Installing systemd service..."

install -m 0644 \
    "$SCRIPT_DIR/contrib/systemd/mailheadercheck.service" \
    "$SERVICE_FILE"

# ---------------------------------------------------------------------------
# Install configuration
# ---------------------------------------------------------------------------

install -d -m 0755 "$CONFIG_DIR"

if [[ -e "$CONFIG_FILE" ]]; then
    log "Configuration already exists, keeping it: $CONFIG_FILE"
else
    log "Installing default configuration..."

    install -m 0644 \
        "$SCRIPT_DIR/examples/config.yaml" \
        "$CONFIG_FILE"
fi

# ---------------------------------------------------------------------------
# Reload systemd
# ---------------------------------------------------------------------------

log "Reloading systemd..."

systemctl daemon-reload

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

log "Installation completed successfully."

echo
echo "mailheadercheck has been installed."
echo
echo "Binary:"
echo "  $INSTALL_DIR/mailheadercheck"
echo
echo "Configuration:"
echo "  $CONFIG_FILE"
echo
echo "Systemd service:"
echo "  $SERVICE_FILE"
echo
echo "To start the service:"
echo "  systemctl enable --now mailheadercheck.service"
echo
echo "To check its status:"
echo "  systemctl status mailheadercheck.service"
