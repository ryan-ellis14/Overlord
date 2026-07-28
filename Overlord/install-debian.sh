#!/bin/bash
set -e

INSTALL_DIR="/opt/overlord"
VENV_DIR="$INSTALL_DIR/venv"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Overlord Kiosk Browser - Debian/Linux Mint Setup ===${NC}"

if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}This script must be run with sudo.${NC}"
    echo "  sudo bash install-debian.sh"
    exit 1
fi

echo -e "${YELLOW}[1/5] Installing system packages...${NC}"
apt-get update -qq 2>&1 | grep -v "NO_PUBKEY\|W: GPG\|The following signatures\|InRelease" || true
apt-get install -y -qq python3-full python3-venv xvfb xdg-utils dbus-x11 2>/dev/null

echo -e "${YELLOW}[2/5] Setting up install directory...${NC}"
mkdir -p "$INSTALL_DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp -r "$SCRIPT_DIR/overlord" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/run_overlord_debian.py" "$INSTALL_DIR/run_overlord.py"
cp "$SCRIPT_DIR/requirements-debian.txt" "$INSTALL_DIR/requirements.txt"

echo -e "${YELLOW}[3/5] Creating virtual environment and installing dependencies...${NC}"
python3 -m venv "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

echo -e "${YELLOW}[4/5] Creating launch script...${NC}"
cat > "$INSTALL_DIR/launch.sh" << 'LAUNCH_EOF'
#!/bin/bash
source /opt/overlord/venv/bin/activate
export QT_QPA_PLATFORM=xcb
exec python3 /opt/overlord/run_overlord.py "$@"
LAUNCH_EOF
chmod +x "$INSTALL_DIR/launch.sh"

echo -e "${YELLOW}[5/5] Installing systemd user service and enabling auto-start...${NC}"
CURRENT_USER="${SUDO_USER:-$USER}"
CURRENT_UID=$(id -u "$CURRENT_USER")
SERVICE_FILE="/etc/systemd/user/overlord@.service"

mkdir -p /etc/systemd/user
cp "$SCRIPT_DIR/systemd/overlord-debian@.service" "$SERVICE_FILE"
chmod 644 "$SERVICE_FILE"

mkdir -p "/home/$CURRENT_USER/.config/systemd/user/default.target.wants"
cp "$SERVICE_FILE" "/home/$CURRENT_USER/.config/systemd/user/overlord@.service"
ln -sf "/home/$CURRENT_USER/.config/systemd/user/overlord@.service" \
    "/home/$CURRENT_USER/.config/systemd/user/default.target.wants/overlord@${CURRENT_USER}.service"
chown -R "$CURRENT_USER:$CURRENT_USER" "/home/$CURRENT_USER/.config/systemd"

XDG_RUNTIME="/run/user/$CURRENT_UID"
if [ -d "$XDG_RUNTIME" ]; then
    su - "$CURRENT_USER" -c "XDG_RUNTIME_DIR=$XDG_RUNTIME systemctl --user daemon-reload" 2>/dev/null || true
    su - "$CURRENT_USER" -c "XDG_RUNTIME_DIR=$XDG_RUNTIME systemctl --user enable overlord@${CURRENT_USER}" 2>/dev/null || true
    echo -e "  ${GREEN}Auto-start enabled for user '$CURRENT_USER'${NC}"
else
    echo -e "  ${YELLOW}Service file installed. Enable auto-start after reboot:${NC}"
    echo -e "    systemctl --user daemon-reload"
    echo -e "    systemctl --user enable overlord@${CURRENT_USER}"
fi

LIGHTDM_CONF="/etc/lightdm/lightdm.conf"
if [ -f "$LIGHTDM_CONF" ]; then
    if ! grep -q "^autologin-user=" "$LIGHTDM_CONF"; then
        if grep -q "^\[SeatDefaults\]" "$LIGHTDM_CONF"; then
            sed -i "/^\[SeatDefaults\]/a autologin-user=$CURRENT_USER\nautologin-user-timeout=0" "$LIGHTDM_CONF"
        else
            printf "\n[SeatDefaults]\nautologin-user=%s\nautologin-user-timeout=0\n" "$CURRENT_USER" >> "$LIGHTDM_CONF"
        fi
        echo -e "  ${GREEN}LightDM auto-login configured for '$CURRENT_USER'${NC}"
    else
        echo -e "  ${GREEN}LightDM auto-login already configured${NC}"
    fi
else
    echo -e "  ${YELLOW}LightDM config not found at $LIGHTDM_CONF - auto-login not configured${NC}"
fi

DESKTOP_FILE="/home/$CURRENT_USER/Desktop/overlord.desktop"
cat > "$DESKTOP_FILE" << 'DESK_EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Overlord
Comment=Multi-View Kiosk Browser
Exec=/opt/overlord/launch.sh
Icon=web-browser
Terminal=false
Categories=Network;WebBrowser;
DESK_EOF
chmod +x "$DESKTOP_FILE"
chown "$CURRENT_USER:$CURRENT_USER" "$DESKTOP_FILE"
echo -e "  ${GREEN}Desktop shortcut created${NC}"

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Overlord (Debian variant) will auto-start on boot for user '$CURRENT_USER'."
echo "After reboot, the login screen will be skipped and Overlord launches fullscreen."
echo ""
echo "To run now without rebooting:"
echo -e "  ${YELLOW}/opt/overlord/launch.sh${NC}"
echo ""
echo "Default PINs:"
echo "  Exit app:        1234"
echo "  Device settings: 5678"
echo "  Kiosk settings:   9999"
