"""
Memory Manager
--------------
يحفظ: المحادثات، المشاريع، الأوامر المستخدمة، الأخطاء المتكررة، والتفضيلات.
التخزين في ملفات JSON بسيطة داخل ~/.cai/memory/
(قابل للترقية لاحقًا لقاعدة بيانات SQLite لو الحجم كبر).
"""

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List


class MemoryManager:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai/memory"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_path = self.base_dir / "conversations.jsonl"
        self.projects_path = self.base_dir / "projects.json"
        self.preferences_path = self.base_dir / "preferences.json"
        self.errors_path = self.base_dir / "errors.jsonl"

    # ---------- محادثات ----------

    def add_message(self, role: str, content: str) -> None:
        entry = {"ts": time.time(), "role": role, "content": content}
        with open(self.conversations_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def recent_messages(self, limit: int = 20) -> List[Dict[str, Any]]:
        if not self.conversations_path.exists():
            return []
        with open(self.conversations_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[-limit:]
        return [json.loads(line) for line in lines]

    # ---------- مشاريع ----------

    def _load_json(self, path: Path, default):
        if not path.exists():
            return default
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return default

    def _save_json(self, path: Path, data) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def remember_project(self, name: str, path: str, meta: Dict[str, Any] = None) -> None:
        projects = self._load_json(self.projects_path, {})
        projects[name] = {"path": path, "meta": meta or {}, "last_used": time.time()}
        self._save_json(self.projects_path, projects)

    def list_projects(self) -> Dict[str, Any]:
        return self._load_json(self.projects_path, {})

    # ---------- تفضيلات ----------

    def set_preference(self, key: str, value: Any) -> None:
        prefs = self._load_json(self.preferences_path, {})
        prefs[key] = value
        self._save_json(self.preferences_path, prefs)

    def get_preference(self, key: str, default: Any = None) -> Any:
        prefs = self._load_json(self.preferences_path, {})
        return prefs.get(key, default)

    # ---------- أخطاء متكررة ----------

    def log_error(self, command: str, error: str) -> None:
        entry = {"ts": time.time(), "command": command, "error": error}
        with open(self.errors_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
