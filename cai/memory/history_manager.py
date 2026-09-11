"""
History Manager
----------------
سجل كامل للأوامر المنفذة (منفصل عن Session وMemory)، يدعم البحث
والاسترجاع بالفهرس (زي !12 في bash)، ومحدود بعدد أقصى قابل للتهيئة.
"""

import json
import os
from pathlib import Path
from typing import List, Optional


class HistoryManager:
    def __init__(self, base_dir: str = None, limit: int = 500):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.history_path = self.base_dir / "history.json"
        self.limit = limit
        self._history: List[str] = self._load()

    def _load(self) -> List[str]:
        if not self.history_path.exists():
            return []
        try:
            with open(self.history_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save(self) -> None:
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self._history[-self.limit:], f, indent=2, ensure_ascii=False)

    def add(self, command: str) -> None:
        if command.strip():
            self._history.append(command)
            self._save()

    def all(self) -> List[str]:
        return list(self._history)

    def last(self, n: int = 10) -> List[str]:
        return self._history[-n:]

    def get_by_index(self, index: int) -> Optional[str]:
        """يدعم فهرسة زي !12 (index يبدأ من 1)."""
        if 1 <= index <= len(self._history):
            return self._history[index - 1]
        return None

    def search(self, keyword: str) -> List[str]:
        return [c for c in self._history if keyword.lower() in c.lower()]

    def clear(self) -> None:
        self._history = []
        self._save()
