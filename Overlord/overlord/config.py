import os

APP_NAME = "Overlord"
APP_VERSION = "1.0.0"

CONFIG_DIR = os.path.expanduser("~/.config/overlord")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
KEY_FILE = os.path.join(CONFIG_DIR, "encryption.key")

DEFAULT_URLS = [
    "https://www.bing.com",
    "https://www.google.com",
    "https://www.wikipedia.org",
]

MAX_URLS = 5

CORNER_SIZE = 160
DOUBLE_TAP_INTERVAL = 1000
TAP_INTERVAL = 1500
SEQUENCE_TIMEOUT = 3000

DEFAULT_EXIT_PIN = "1234"
DEFAULT_SETTINGS_PIN = "5678"
DEFAULT_KIOSK_SETTINGS_PIN = "9999"

GESTURE_CORNER_DOUBLE_TAP = "corner_double_tap"
GESTURE_FIVE_TAP_ANYWHERE = "five_tap_anywhere"
GESTURE_CORNER_SEQUENCE = "corner_sequence"
GESTURE_TYPES = [
    GESTURE_CORNER_DOUBLE_TAP,
    GESTURE_FIVE_TAP_ANYWHERE,
    GESTURE_CORNER_SEQUENCE,
]

GESTURE_LABELS = {
    GESTURE_CORNER_DOUBLE_TAP: "Double-Tap Corner",
    GESTURE_FIVE_TAP_ANYWHERE: "Five Quick Taps",
    GESTURE_CORNER_SEQUENCE: "Corner Sequence (TLx2 then BRx2)",
}

PREF_GESTURE_TYPE = "gesture_type"
PREF_URLS = "multiview_urls"
PREF_AUTO_UPDATE = "auto_update_enabled"

SWIPE_THRESHOLD = 50

GITHUB_OWNER = "ryan-ellis14"
GITHUB_REPO = "Overlord"
UPDATE_BRANCH = "main"
UPDATE_CHECK_INTERVAL_MS = 10 * 60 * 1000
UPDATE_CHECK_TIMEOUT_S = 15

GITHUB_API_COMMIT_URL = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/commits/{UPDATE_BRANCH}"
)
GITHUB_RAW_CONFIG_URL = (
    f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}/{UPDATE_BRANCH}"
    f"/Overlord/overlord/config.py"
)

SOURCE_REPO_DIR = "/opt/overlord-repo"
INSTALL_DIR = "/opt/overlord"
UPDATE_SERVICE_TEMPLATE = "overlord-update@.service"
