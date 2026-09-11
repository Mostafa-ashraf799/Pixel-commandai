"""
Config Manager
--------------
يدير كل إعدادات CommandAI (cai): الموديل الحالي، الـ Provider الحالي،
وضع التشغيل (Safe / Smart / Expert)، الثيم، وأي تفضيلات عامة.

الإعدادات بتتخزن في ملف JSON داخل مجلد المستخدم:
~/.cai/config.json
"""

import json
import os
from pathlib import Path
from typing import Any, Dict


DEFAULT_CONFIG: Dict[str, Any] = {
    "version": "1.0.0",
    "provider": "pixel",
    "model": "",  # Pixel CommandAI: model choice lives server-side, not in client config
    "mode": "smart",          # safe | smart | expert
    "theme": "dark",          # dark | light | cyberpunk | matrix | hacker
    "language": "auto",       # auto | ar | en
    "confirm_dangerous": True,
    "confirm_warning": True,
    "history_limit": 500,
    "log_level": "info",
}


class ConfigManager:
    """مسؤول عن قراءة/كتابة إعدادات cai بشكل آمن ومركزي."""

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai"))
        self.config_path = self.base_dir / "config.json"
        self._config: Dict[str, Any] = {}
        self._ensure_dirs()
        self.load()

    def _ensure_dirs(self) -> None:
        self.base_dir.mkdir(parents=True, exist_ok=True)
        (self.base_dir / "logs").mkdir(exist_ok=True)
        (self.base_dir / "sessions").mkdir(exist_ok=True)
        (self.base_dir / "memory").mkdir(exist_ok=True)
        (self.base_dir / "plugins").mkdir(exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                self._config = {**DEFAULT_CONFIG, **loaded}
            except (json.JSONDecodeError, OSError):
                self._config = dict(DEFAULT_CONFIG)
        else:
            self._config = dict(DEFAULT_CONFIG)
            self.save()
        return self._config

    def save(self) -> None:
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(self._config, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def set(self, key: str, value: Any, persist: bool = True) -> None:
        self._config[key] = value
        if persist:
            self.save()

    def all(self) -> Dict[str, Any]:
        return dict(self._config)

    def reset(self) -> None:
        self._config = dict(DEFAULT_CONFIG)
        self.save()
