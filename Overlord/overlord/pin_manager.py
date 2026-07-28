import json
import os
import logging
import base64

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .config import (
    CONFIG_DIR,
    CONFIG_FILE,
    KEY_FILE,
    DEFAULT_EXIT_PIN,
    DEFAULT_SETTINGS_PIN,
    DEFAULT_KIOSK_SETTINGS_PIN,
    PREF_GESTURE_TYPE,
    GESTURE_CORNER_DOUBLE_TAP,
    PREF_URLS,
    DEFAULT_URLS,
)

logger = logging.getLogger("overlord")


class PinManager:

    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self._key = self._load_or_generate_key()
        self._config = self._load_config()
        self._initialize_defaults()

    def _load_or_generate_key(self):
        if os.path.exists(KEY_FILE):
            with open(KEY_FILE, "rb") as f:
                return f.read()
        key = AESGCM.generate_key(bit_length=256)
        with open(KEY_FILE, "wb") as f:
            f.write(key)
        os.chmod(KEY_FILE, 0o600)
        return key

    def _load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Error loading config: %s", e)
        return {}

    def _save_config(self):
        with open(CONFIG_FILE, "w") as f:
            json.dump(self._config, f, indent=2)
        os.chmod(CONFIG_FILE, 0o600)

    def _initialize_defaults(self):
        if "exit_pin" not in self._config:
            self._config["exit_pin"] = self._encrypt_pin(DEFAULT_EXIT_PIN)
            logger.debug("Set default exit PIN")
        if "settings_pin" not in self._config:
            self._config["settings_pin"] = self._encrypt_pin(DEFAULT_SETTINGS_PIN)
            logger.debug("Set default settings PIN")
        if "kiosk_settings_pin" not in self._config:
            self._config["kiosk_settings_pin"] = self._encrypt_pin(DEFAULT_KIOSK_SETTINGS_PIN)
            logger.debug("Set default kiosk settings PIN")
        if PREF_GESTURE_TYPE not in self._config:
            self._config[PREF_GESTURE_TYPE] = GESTURE_CORNER_DOUBLE_TAP
        if PREF_URLS not in self._config:
            self._config[PREF_URLS] = DEFAULT_URLS
        self._save_config()

    def _encrypt_pin(self, pin: str) -> str:
        aesgcm = AESGCM(self._key)
        nonce = os.urandom(12)
        ciphertext = aesgcm.encrypt(nonce, pin.encode("utf-8"), None)
        return base64.b64encode(nonce + ciphertext).decode("utf-8")

    def _decrypt_pin(self, encrypted: str) -> str | None:
        try:
            raw = base64.b64decode(encrypted.encode("utf-8"))
            nonce = raw[:12]
            ciphertext = raw[12:]
            aesgcm = AESGCM(self._key)
            return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
        except Exception as e:
            logger.error("Error decrypting PIN: %s", e)
            return None

    def get_exit_pin(self) -> str:
        pin = self._decrypt_pin(self._config.get("exit_pin", ""))
        if pin is None:
            logger.warning("Exit PIN not found, using default")
            return DEFAULT_EXIT_PIN
        return pin

    def get_settings_pin(self) -> str:
        pin = self._decrypt_pin(self._config.get("settings_pin", ""))
        if pin is None:
            logger.warning("Settings PIN not found, using default")
            return DEFAULT_SETTINGS_PIN
        return pin

    def get_kiosk_settings_pin(self) -> str:
        pin = self._decrypt_pin(self._config.get("kiosk_settings_pin", ""))
        if pin is None:
            logger.warning("Kiosk settings PIN not found, using default")
            return DEFAULT_KIOSK_SETTINGS_PIN
        return pin

    def save_exit_pin(self, pin: str):
        self._config["exit_pin"] = self._encrypt_pin(pin)
        self._save_config()

    def save_settings_pin(self, pin: str):
        self._config["settings_pin"] = self._encrypt_pin(pin)
        self._save_config()

    def save_kiosk_settings_pin(self, pin: str):
        self._config["kiosk_settings_pin"] = self._encrypt_pin(pin)
        self._save_config()

    def get_urls(self) -> list[str]:
        return list(self._config.get(PREF_URLS, DEFAULT_URLS))

    def save_urls(self, urls: list[str]):
        self._config[PREF_URLS] = urls
        self._save_config()

    def get_gesture_type(self) -> str:
        return self._config.get(PREF_GESTURE_TYPE, GESTURE_CORNER_DOUBLE_TAP)

    def save_gesture_type(self, gesture_type: str):
        self._config[PREF_GESTURE_TYPE] = gesture_type
        self._save_config()
