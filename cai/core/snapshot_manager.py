"""
Snapshot / Undo System
------------------------
ميزة أمان مهمة جدًا: قبل ما الـ Agent يعدّل أي ملف (عبر edit أو do أو team)،
يتم أخذ نسخة احتياطية تلقائية (Snapshot) قبل التعديل. لو النتيجة مش عاجبة
المستخدم، يقدر يرجع للنسخة القديمة فورًا بأمر واحد (undo).

ده بيحل مشكلة شائعة جدًا: "الـ AI عدّل الملف وخربه وأنا مش فاكر الأصلي كان إيه".
"""

import hashlib
import json
import os
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class SnapshotEntry:
    id: str
    original_path: str
    snapshot_path: str
    ts: float
    reason: str


class SnapshotManager:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai/snapshots"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.index_path = self.base_dir / "index.json"

    def _load_index(self) -> List[dict]:
        if not self.index_path.exists():
            return []
        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return []

    def _save_index(self, index: List[dict]) -> None:
        with open(self.index_path, "w", encoding="utf-8") as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def _make_snapshot_id(self, file_path: str) -> str:
        timestamp = str(time.time())
        raw = f"{file_path}-{timestamp}"
        return hashlib.sha1(raw.encode()).hexdigest()[:12]

    def snapshot_before_edit(self, file_path: str, reason: str = "قبل تعديل الـ AI") -> Optional[str]:
        """يأخذ نسخة احتياطية من ملف قبل تعديله. يرجع snapshot_id أو None لو الملف غير موجود."""
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            return None

        snapshot_id = self._make_snapshot_id(file_path)
        snapshot_file = self.base_dir / f"{snapshot_id}_{path.name}"
        shutil.copy2(path, snapshot_file)

        index = self._load_index()
        index.append({
            "id": snapshot_id,
            "original_path": str(path.resolve()),
            "snapshot_path": str(snapshot_file),
            "ts": time.time(),
            "reason": reason,
        })
        self._save_index(index)

        return snapshot_id

    def list_snapshots(self, file_path: Optional[str] = None, limit: int = 20) -> List[SnapshotEntry]:
        index = self._load_index()
        if file_path:
            resolved = str(Path(file_path).resolve())
            index = [e for e in index if e["original_path"] == resolved]
        index = sorted(index, key=lambda e: e["ts"], reverse=True)[:limit]
        return [SnapshotEntry(**e) for e in index]

    def restore(self, snapshot_id: str) -> str:
        index = self._load_index()
        entry = next((e for e in index if e["id"] == snapshot_id), None)
        if not entry:
            return f"لم يتم العثور على نسخة احتياطية بالمعرف: {snapshot_id}"

        snapshot_path = Path(entry["snapshot_path"])
        if not snapshot_path.exists():
            return "ملف النسخة الاحتياطية غير موجود على القرص (ربما تم حذفه)."

        shutil.copy2(snapshot_path, entry["original_path"])
        return f"تم استرجاع {entry['original_path']} إلى حالته وقت {time.ctime(entry['ts'])}"

    def undo_last(self, file_path: str) -> str:
        """يرجع آخر نسخة محفوظة لملف معين مباشرة، بدون الحاجة لمعرفة الـ snapshot_id."""
        snapshots = self.list_snapshots(file_path=file_path, limit=1)
        if not snapshots:
            return f"لا توجد نسخ احتياطية محفوظة لـ {file_path}"
        return self.restore(snapshots[0].id)

    def cleanup_old(self, keep_days: int = 30) -> int:
        """ينظف النسخ الاحتياطية الأقدم من عدد أيام معين، يرجع عدد الملفات المحذوفة."""
        cutoff = time.time() - (keep_days * 86400)
        index = self._load_index()
        remaining = []
        removed_count = 0

        for entry in index:
            if entry["ts"] < cutoff:
                snapshot_path = Path(entry["snapshot_path"])
                if snapshot_path.exists():
                    snapshot_path.unlink()
                removed_count += 1
            else:
                remaining.append(entry)

        self._save_index(remaining)
        return removed_count
