"""
Configuration module for BlazeDemo Regression Suite.

Reads settings from settings.json and exposes typed properties.
Supports environment variable overrides for CI/CD integration.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List


_SETTINGS_PATH = Path(__file__).parent / "settings.json"


class Config:
    """
    Singleton configuration reader.

    Merges values from settings.json with optional environment-variable
    overrides so the same suite can run in local, staging, and CI contexts
    without code changes.
    """

    _instance: "Config | None" = None
    _data: dict

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Load and validate the JSON settings file."""
        with open(_SETTINGS_PATH, encoding="utf-8") as fh:
            self._data = json.load(fh)

    def _get(self, key: str, env_var: str | None = None, default=None):
        """Return env-var override if set, else JSON value, else default."""
        if env_var and (val := os.environ.get(env_var)):
            return val
        return self._data.get(key, default)

    # ------------------------------------------------------------------
    # Public properties
    # ------------------------------------------------------------------

    @property
    def base_url(self) -> str:
        return self._get("base_url", "BLAZEDEMO_BASE_URL", "https://blazedemo.com")

    @property
    def explicit_wait(self) -> int:
        return int(self._get("explicit_wait", "EXPLICIT_WAIT", 15))

    @property
    def page_load_timeout(self) -> int:
        return int(self._get("page_load_timeout", "PAGE_LOAD_TIMEOUT", 30))

    @property
    def screenshot_dir(self) -> Path:
        raw = self._get("screenshot_dir", "SCREENSHOT_DIR", "reports/screenshots")
        path = Path(raw)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_file(self) -> Path:
        raw = self._get("log_file", "LOG_FILE", "reports/test_run.log")
        path = Path(raw)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def supported_browsers(self) -> List[str]:
        return self._data.get("supported_browsers", ["chrome"])

    @property
    def retry_attempts(self) -> int:
        return int(self._get("retry_attempts", default=3))

    @property
    def retry_delay(self) -> float:
        return float(self._get("retry_delay", default=1))


# Convenience singleton instance
cfg = Config()
