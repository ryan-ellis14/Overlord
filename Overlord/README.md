# Overlord — Multi-View Kiosk Browser

Full-screen, gesture-locked kiosk browser that displays multiple web pages with swipeable navigation. Designed for unattended public displays, digital signage, and locked-down kiosk deployments.

## Architecture

Overlord v2.0 is split into two platform-specific variants sharing a common core:

```
overlord/
  config.py              # Shared constants (URLs, PINs, gestures, timing)
  pin_manager.py         # Shared AES-256 encrypted PIN and settings storage
  debian/                # Debian/Linux Mint variant (PyQt6 + WebEngine)
    main.py              # Full-screen kiosk window with QStackedWidget
    webview_page.py      # Chromium-based webview (QWebEngineView)
    pin_dialog.py        # Modal PIN entry numpad
    settings_window.py   # URL, PIN, and gesture configuration UI
    splash_window.py     # Launch screen with auto-start
    gesture_handler.py   # Qt-based corner tap / five-tap / sequence detection
    ui/                  # Custom pill buttons and page indicator widgets
  pi/                    # Raspberry Pi OS variant (pywebview + WebKitGTK)
    main.py              # pywebview window controller with overlay injection
    api.py               # JS bridge API exposing config to the injected UI
    ui/
      overlay.js         # Injected nav bar, gesture detection, and PIN dialog
      settings.html      # Full-page kiosk settings (loaded as local file)
```

## Variants

| | Debian/Linux Mint | Raspberry Pi OS (64-bit) |
|---|---|---|
| **Engine** | PyQt6-WebEngine (Chromium) | pywebview + WebKitGTK |
| **Display** | X11 (xcb) | Wayland or X11 (auto-detected) |
| **UI Toolkit** | PyQt6 widgets | Injected HTML/CSS/JS |
| **DM** | LightDM | LightDM (or raspi-config) |
| **Install Script** | `install-debian.sh` | `install-raspberrypi.sh` |

## Installation

### Debian / Linux Mint

```bash
sudo bash install-debian.sh
```

Installs PyQt6-WebEngine, sets up a systemd user service, and configures LightDM auto-login.

### Raspberry Pi OS (64-bit, Bookworm+)

```bash
sudo bash install-raspberrypi.sh
```

Installs WebKitGTK system libraries, sets up a systemd user service, and configures auto-login. Detects Wayland vs X11 automatically at launch.

## Usage

After installation, Overlord launches fullscreen on boot. Navigate between pages using the bottom bar or keyboard arrows.

### Unlock Gestures

A gesture unlocks the PIN dialog. Three modes available (configurable):

| Gesture | Description |
|---|---|
| **Double-Tap Corner** | Double-tap any screen corner within 1 second |
| **Five Quick Taps** | Tap anywhere 5 times within 1.5 seconds |
| **Corner Sequence** | Double-tap top-left, then double-tap bottom-right |

### Default PINs

| Action | PIN |
|---|---|
| Exit application | `1234` |
| Open device settings | `5678` |
| Open kiosk settings | `9999` |

### Secret Unlock (Bottom Bar)

Five rapid taps on the right arrow button also triggers the PIN dialog.

### Keyboard Shortcuts (Debian variant)

- `Esc` — Open PIN dialog
- `Left Arrow` — Previous page
- `Right Arrow` — Next page

## Configuration

All config is stored in `~/.config/overlord/`:

- `config.json` — URLs, gesture type, encrypted PINs
- `encryption.key` — AES-256-GCM key (file permission 0600)

### Kiosk Settings

Unlock with the kiosk settings PIN (`9999` default) to modify:
- Up to 5 display URLs
- Gesture unlock type
- All three PINs (requires current PIN to change)

## File Reference

### Root Level

| File | Description |
|---|---|
| `install-debian.sh` | System installer for Debian/Linux Mint |
| `install-raspberrypi.sh` | System installer for Raspberry Pi OS |
| `run_overlord_debian.py` | Debian entry point |
| `run_overlord_pi.py` | Raspberry Pi entry point |
| `requirements-debian.txt` | PyQt6 + WebEngine + cryptography |
| `requirements-pi.txt` | pywebview + cryptography |
| `setup.py` | Python package (shared core only) |

### Shared Core (`overlord/`)

| File | Description |
|---|---|
| `config.py` | App constants: name, version, default URLs, PIN defaults, gesture timing, UI sizing |
| `pin_manager.py` | AES-256-GCM encrypted config storage, PIN CRUD, URL/gesture persistence |

### Debian Variant (`overlord/debian/`)

| File | Description |
|---|---|
| `main.py` | Main kiosk window: fullscreen QStackedWidget, nav bar, gesture binding, screensaver inhibition |
| `webview_page.py` | QWebEngineView wrapper with SSL bypass and custom user agent |
| `pin_dialog.py` | Frameless modal with 4-digit numpad, dot indicator, and PIN routing |
| `settings_window.py` | Scrollable settings dialog: URL management, PIN changes, gesture selection |
| `splash_window.py` | Centered launch screen with auto-start (500ms) |
| `gesture_handler.py` | QObject-based gesture detector for three unlock modes |
| `ui/pill_button.py` | Custom painted pill-shaped arrow button widget |
| `ui/page_indicator.py` | "1 / N" page counter widget |

### Raspberry Pi Variant (`overlord/pi/`)

| File | Description |
|---|---|
| `main.py` | pywebview controller: creates window, injects overlay on page load, manages lifecycle |
| `api.py` | Exposed JS bridge: navigation, PIN checking, settings CRUD, exit, device settings |
| `ui/overlay.js` | Self-contained injected UI: nav bar, gesture detection, PIN dialog (all inline styles) |
| `ui/settings.html` | Full-page kiosk settings with embedded JS using pywebview bridge |

## Systemd Services

Both variants install a systemd user service at `/etc/systemd/user/overlord@.service`. The service launches `/opt/overlord/launch.sh` and auto-restarts on failure (5 second delay).

### Managing the Service

```bash
systemctl --user status overlord@$(whoami)
systemctl --user restart overlord@$(whoami)
systemctl --user stop overlord@$(whoami)
journalctl --user -u overlord@$(whoami) -f
```

## Build From Source

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements-debian.txt   # or requirements-pi.txt
python3 run_overlord_debian.py          # or run_overlord_pi.py
```

## License

Proprietary — see license file for details.
