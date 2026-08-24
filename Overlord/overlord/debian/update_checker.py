import json
import logging
import re
import subprocess
import urllib.request
import urllib.error

from PyQt6.QtCore import QThread, pyqtSignal

from ..config import (
    APP_VERSION,
    GITHUB_API_COMMIT_URL,
    GITHUB_RAW_CONFIG_URL,
    SOURCE_REPO_DIR,
    UPDATE_BRANCH,
    UPDATE_CHECK_INTERVAL_MS,
    UPDATE_CHECK_TIMEOUT_S,
)

logger = logging.getLogger("overlord")

_VERSION_RE = re.compile(r'^APP_VERSION\s*=\s*"([^"]+)"', re.MULTILINE)


class UpdateInfo:

    def __init__(
        self,
        available: bool,
        local_version: str,
        remote_version: str,
        local_sha: str,
        remote_sha: str,
    ):
        self.available = available
        self.local_version = local_version
        self.remote_version = remote_version
        self.local_sha = local_sha
        self.remote_sha = remote_sha

    def short_local_sha(self) -> str:
        return self.local_sha[:7] if self.local_sha else "unknown"

    def short_remote_sha(self) -> str:
        return self.remote_sha[:7] if self.remote_sha else "unknown"


class UpdateChecker(QThread):

    update_result = pyqtSignal(object)
    check_failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._interval_ms = UPDATE_CHECK_INTERVAL_MS

    def run(self):
        logger.info("Update checker started (interval=%dms)", self._interval_ms)
        self._do_check()
        while not self.isInterruptionRequested():
            ms_remaining = self._interval_ms
            while ms_remaining > 0 and not self.isInterruptionRequested():
                self.msleep(min(ms_remaining, 500))
                ms_remaining -= 500
            if self.isInterruptionRequested():
                break
            self._do_check()
        logger.info("Update checker stopped")

    def check_now(self):
        if not self.isRunning():
            self.start()
        else:
            self._do_check()

    def _do_check(self):
        try:
            remote_sha = self._fetch_remote_sha()
            remote_version = self._fetch_remote_version()
            local_sha = self._read_local_sha()
            local_version = APP_VERSION

            available = bool(remote_sha) and remote_sha != local_sha
            info = UpdateInfo(
                available=available,
                local_version=local_version,
                remote_version=remote_version or "unknown",
                local_sha=local_sha or "",
                remote_sha=remote_sha or "",
            )
            logger.debug(
                "Update check: local=%s remote=%s available=%s",
                info.short_local_sha(),
                info.short_remote_sha(),
                available,
            )
            self.update_result.emit(info)
        except Exception as e:
            logger.warning("Update check failed: %s", e)
            self.check_failed.emit(str(e))

    def _fetch_remote_sha(self) -> str:
        req = urllib.request.Request(
            GITHUB_API_COMMIT_URL,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "Overlord-Kiosk",
            },
        )
        with urllib.request.urlopen(req, timeout=UPDATE_CHECK_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("sha", "") or ""

    def _fetch_remote_version(self) -> str:
        req = urllib.request.Request(
            GITHUB_RAW_CONFIG_URL,
            headers={"User-Agent": "Overlord-Kiosk"},
        )
        with urllib.request.urlopen(req, timeout=UPDATE_CHECK_TIMEOUT_S) as resp:
            content = resp.read().decode("utf-8")
        match = _VERSION_RE.search(content)
        return match.group(1) if match else ""

    def _read_local_sha(self) -> str:
        try:
            result = subprocess.run(
                ["git", "-C", SOURCE_REPO_DIR, "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            logger.debug("git rev-parse failed: %s", e)
        return ""
