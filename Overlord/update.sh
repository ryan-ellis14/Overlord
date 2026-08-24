#!/bin/bash
set -e

# Overlord update script - run as root by overlord-update@.service
# Usage: update.sh <username>
#
# Pulls latest code from GitHub, re-runs the installer, and restarts
# the user's Overlord kiosk service.

REPO_DIR="/opt/overlord-repo"
INSTALL_SCRIPT="$REPO_DIR/Overlord/install-debian.sh"
LOG_FILE="/tmp/overlord-update.log"
STATUS_FILE="/tmp/overlord-update-status"
BRANCH="main"
SERVICE_USER="${1:-overlord}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() {
    echo -e "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE" >&2
}

set_status() {
    echo "$1" > "$STATUS_FILE"
    log "$1"
}

fail() {
    log "${RED}UPDATE FAILED: $1${NC}"
    set_status "FAILED: $1"
    exit 1
}

trap 'fail "Unexpected error on line $LINENO"' ERR

if [ "$(id -u)" -ne 0 ]; then
    fail "Must be run as root"
fi

if [ ! -d "$REPO_DIR/.git" ]; then
    fail "$REPO_DIR is not a git repository"
fi

log "${GREEN}=== Overlord Update Started (user=$SERVICE_USER) ===${NC}"
rm -f "$STATUS_FILE"
: > "$LOG_FILE"

set_status "Pulling latest code from GitHub..."

cd "$REPO_DIR"
git fetch origin "$BRANCH" >> "$LOG_FILE" 2>&1 || fail "git fetch failed"
git reset --hard "origin/$BRANCH" >> "$LOG_FILE" 2>&1 || fail "git reset failed"

LOCAL_SHA=$(git rev-parse --short HEAD)
log "Now at commit $LOCAL_SHA"

set_status "Reinstalling Overlord..."

if [ ! -f "$INSTALL_SCRIPT" ]; then
    fail "install-debian.sh not found at $INSTALL_SCRIPT"
fi

bash "$INSTALL_SCRIPT" >> "$LOG_FILE" 2>&1 || fail "Installer returned an error"

set_status "Restarting kiosk service..."

SERVICE_UID=$(id -u "$SERVICE_USER" 2>/dev/null || echo "")
if [ -z "$SERVICE_UID" ]; then
    fail "User '$SERVICE_USER' does not exist"
fi

XDG_RUNTIME="/run/user/$SERVICE_UID"
if [ ! -d "$XDG_RUNTIME" ]; then
    log "${YELLOW}Warning: $XDG_RUNTIME not present; service may not restart until next login${NC}"
    set_status "Update complete. Service will restart on next login."
    log "${GREEN}=== Update Complete (no live restart) ===${NC}"
    exit 0
fi

runuser -u "$SERVICE_USER" -- env \
    XDG_RUNTIME_DIR="$XDG_RUNTIME" \
    DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME/bus" \
    systemctl --user restart "overlord@${SERVICE_USER}.service" >> "$LOG_FILE" 2>&1 \
    || fail "Could not restart user service"

set_status "Update complete. Kiosk restarting..."
log "${GREEN}=== Update Complete ===${NC}"

# Keep status file briefly visible to the dialog, then clean up
sleep 3
rm -f "$STATUS_FILE"

exit 0
