#!/bin/bash
set -e
cd /tmp

INSTALL_DIR="/opt/overlord"
VENV_DIR="$INSTALL_DIR/venv"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== Overlord Kiosk Browser - Raspberry Pi OS Setup ===${NC}"
echo -e "${YELLOW}Variant: GTK3 + WebKitGTK (lightweight)${NC}"

if [ "$(id -u)" -ne 0 ]; then
    echo -e "${RED}This script must be run with sudo.${NC}"
    echo "  sudo bash install-raspberrypi.sh"
    exit 1
fi

echo -e "${YELLOW}[1/6] Installing system packages...${NC}"
apt-get update -qq 2>&1 | grep -v "NO_PUBKEY\|W: GPG\|The following signatures\|InRelease" || true
apt-get install -y -qq python3-full python3-venv python3-pip \
    python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1 \
    libjavascriptcoregtk-4.1-0 libwebkit2gtk-4.1-0 \
    xdg-utils dbus-x11 2>/dev/null

echo -e "${YELLOW}[2/6] Setting up install directory...${NC}"
mkdir -p "$INSTALL_DIR"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp -r "$SCRIPT_DIR/overlord" "$INSTALL_DIR/"
cp "$SCRIPT_DIR/run_overlord_pi.py" "$INSTALL_DIR/run_overlord.py"
cp "$SCRIPT_DIR/requirements-pi.txt" "$INSTALL_DIR/requirements.txt"

echo -e "${YELLOW}[3/6] Creating virtual environment and installing dependencies...${NC}"
python3 -m venv --system-site-packages "$VENV_DIR"
"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$INSTALL_DIR/requirements.txt" -q

echo -e "${YELLOW}[4/6] Creating launch script...${NC}"
cat > "$INSTALL_DIR/launch.sh" << 'LAUNCH_EOF'
#!/bin/bash
source /opt/overlord/venv/bin/activate

SESSION_TYPE=$(loginctl show-session $(loginctl | grep $(whoami) | awk '{print $1}') -p Type --value 2>/dev/null || echo "")

if [ "$SESSION_TYPE" = "wayland" ]; then
    export GDK_BACKEND=wayland
else
    export GDK_BACKEND=x11
    export DISPLAY=:0
    export XAUTHORITY="${HOME}/.Xauthority"
fi

exec python3 /opt/overlord/run_overlord.py "$@"
LAUNCH_EOF
chmod +x "$INSTALL_DIR/launch.sh"

echo -e "${YELLOW}[5/6] Installing systemd user service and enabling auto-start...${NC}"
CURRENT_USER="${SUDO_USER:-$USER}"
CURRENT_UID=$(id -u "$CURRENT_USER")
SERVICE_FILE="/etc/systemd/user/overlord@.service"

mkdir -p /etc/systemd/user
cp "$SCRIPT_DIR/systemd/overlord-pi@.service" "$SERVICE_FILE"
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

echo -e "${YELLOW}[6/6] Configuring auto-login and desktop shortcut...${NC}"
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
    echo -e "  ${YELLOW}On Raspberry Pi OS, auto-login may be configured via raspi-config:${NC}"
    echo -e "    ${YELLOW}sudo raspi-config -> System Options -> Boot / Auto Login${NC}"
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
echo "Overlord (Raspberry Pi variant) will auto-start on boot for user '$CURRENT_USER'."
echo "After reboot, the login screen will be skipped and Overlord launches fullscreen."
echo ""
echo "To run now without rebooting:"
echo -e "  ${YELLOW}/opt/overlord/launch.sh${NC}"
echo ""
echo "Default PINs:"
echo "  Exit app:        1234"
echo "  Device settings: 5678"
echo "  Kiosk settings:   9999"
