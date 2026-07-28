import json
import os
import logging

logger = logging.getLogger("overlord-kpi")

KPI_CONFIG_DIR = os.path.expanduser("~/.config/overlord-kpi")
KPI_CONFIG_FILE = os.path.join(KPI_CONFIG_DIR, "config.json")

DEFAULT_ROTATION_INTERVAL = 60


class KpiConfig:

    def __init__(self):
        os.makedirs(KPI_CONFIG_DIR, exist_ok=True)
        self._config = self._load_config()
        self._initialize_defaults()

    def _load_config(self):
        if os.path.exists(KPI_CONFIG_FILE):
            try:
                with open(KPI_CONFIG_FILE, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError) as e:
                logger.error("Error loading KPI config: %s", e)
        return {}

    def _save_config(self):
        with open(KPI_CONFIG_FILE, "w") as f:
            json.dump(self._config, f, indent=2)

    def _initialize_defaults(self):
        changed = False
        if "left_screen_url" not in self._config:
            self._config["left_screen_url"] = ""
            changed = True
        if "rotation_urls" not in self._config:
            self._config["rotation_urls"] = []
            changed = True
        if "rotation_interval" not in self._config:
            self._config["rotation_interval"] = DEFAULT_ROTATION_INTERVAL
            changed = True
        if changed:
            self._save_config()

    @property
    def is_configured(self):
        return bool(self._config.get("rotation_urls", []))

    def get_left_screen_url(self):
        return self._config.get("left_screen_url", "")

    def get_rotation_urls(self):
        return list(self._config.get("rotation_urls", []))

    def get_rotation_interval(self):
        return int(self._config.get("rotation_interval", DEFAULT_ROTATION_INTERVAL))

    def save_config(self, left_url, rotation_urls, rotation_interval):
        self._config["left_screen_url"] = left_url
        self._config["rotation_urls"] = rotation_urls
        self._config["rotation_interval"] = rotation_interval
        self._save_config()
        logger.info("KPI config saved: left=%s, %d rotation URLs, %ds interval",
                     "enabled" if left_url else "disabled",
                     len(rotation_urls), rotation_interval)