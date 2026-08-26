#!/usr/bin/env bash

set -Eeuo pipefail

INSTALL_DIR="/usr/local/sbin"
CONFIG_DIR="/etc/mailheadercheck"
CONFIG_FILE="$CONFIG_DIR/config.yaml"
SERVICE_FILE="/etc/systemd/system/mailheadercheck.service"

BINARY="$INSTALL_DIR/mailheadercheck"
LIBRARY_DIR="$INSTALL_DIR/mailheaderchecklib"

REMOVE_CONFIG=false

log() {
    echo "[INFO] $*"
}

warn() {
    echo "[WARN] $*" >&2
}

error() {
    echo "[ERROR] $*" >&2
}

die() {
    error "$*"
    exit 1
}

trap 'error "Uninstallation failed at line $LINENO: $BASH_COMMAND"' ERR

# ---------------------------------------------------------------------------
# Help
# ---------------------------------------------------------------------------

usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Uninstall mailheadercheck.

Options:
    --remove-config    Remove /etc/mailheadercheck and its configuration.
    -h, --help         Show this help message.

By default, the configuration is preserved.
System packages and Python packages are never removed.
EOF
}

# ---------------------------------------------------------------------------
# Arguments
# ---------------------------------------------------------------------------

while [[ $# -gt 0 ]]; do
    case "$1" in
        --remove-config)
            REMOVE_CONFIG=true
            shift
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            die "Unknown option: $1"
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Root check
# ---------------------------------------------------------------------------

if [[ "${EUID}" -ne 0 ]]; then
    die "This uninstaller must be run as root. Please run: sudo $0"
fi

# ---------------------------------------------------------------------------
# Confirm
# ---------------------------------------------------------------------------

echo
echo "This will uninstall mailheadercheck."
echo
echo "The following will be removed:"
echo "  $BINARY"
echo "  $LIBRARY_DIR"
echo "  $SERVICE_FILE"

if [[ "$REMOVE_CONFIG" == true ]]; then
    echo "  $CONFIG_DIR"
else
    echo
    echo "Configuration will be PRESERVED:"
    echo "  $CONFIG_DIR"
fi

echo
echo "System packages and Python packages will NOT be removed."
echo

read -r -p "Continue? [y/N] " answer

case "$answer" in
    y|Y|yes|YES)
        ;;
    *)
        log "Uninstallation cancelled."
        exit 0
        ;;
esac

# ---------------------------------------------------------------------------
# Stop and disable systemd service
# ---------------------------------------------------------------------------

if systemctl list-unit-files \
    --full --no-legend 2>/dev/null |
    awk '{print $1}' |
    grep -Fxq "mailheadercheck.service"; then

    log "Stopping mailheadercheck service..."

    if systemctl is-active --quiet mailheadercheck.service; then
        systemctl stop mailheadercheck.service
    fi

    log "Disabling mailheadercheck service..."

    if systemctl is-enabled --quiet mailheadercheck.service 2>/dev/null; then
        systemctl disable mailheadercheck.service
    fi
else
    log "mailheadercheck service is not registered with systemd."
fi

# ---------------------------------------------------------------------------
# Remove systemd service
# ---------------------------------------------------------------------------

if [[ -e "$SERVICE_FILE" ]]; then
    log "Removing systemd service..."

    rm -f "$SERVICE_FILE"
else
    log "Systemd service file not found, skipping."
fi

systemctl daemon-reload

# ---------------------------------------------------------------------------
# Remove application
# ---------------------------------------------------------------------------

if [[ -e "$BINARY" ]]; then
    log "Removing executable..."

    rm -f "$BINARY"
else
    log "Executable not found, skipping."
fi

if [[ -e "$LIBRARY_DIR" ]]; then
    log "Removing application library..."

    rm -rf "$LIBRARY_DIR"
else
    log "Application library not found, skipping."
fi

# ---------------------------------------------------------------------------
# Remove configuration
# ---------------------------------------------------------------------------

if [[ "$REMOVE_CONFIG" == true ]]; then
    if [[ -d "$CONFIG_DIR" ]]; then
        log "Removing configuration directory..."

        rm -rf "$CONFIG_DIR"
    else
        log "Configuration directory not found, skipping."
    fi
else
    log "Preserving configuration: $CONFIG_DIR"
fi

# ---------------------------------------------------------------------------
# Clean up empty installation directory
# ---------------------------------------------------------------------------

if [[ -d "$INSTALL_DIR" ]] && [[ -z "$(find "$INSTALL_DIR" -maxdepth 1 -type f -name 'mailheadercheck' -print -quit)" ]]; then
    # Do not remove /usr/local/sbin itself. It is a shared system directory.
    :
fi

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------

log "Uninstallation completed successfully."

echo
echo "mailheadercheck has been uninstalled."
echo
echo "System packages were NOT removed."
echo "Python packages were NOT removed."

if [[ "$REMOVE_CONFIG" == true ]]; then
    echo "Configuration was removed."
else
    echo "Configuration was preserved at:"
    echo "  $CONFIG_FILE"
    echo
    echo "To remove it later:"
    echo "  sudo $0 --remove-config"
fi
