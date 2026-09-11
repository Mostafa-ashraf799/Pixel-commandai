"""
Session Manager
---------------
يحفظ كل جلسة عمل (Session) بشكل مستقل: تاريخ البدء، الأوامر المنفذة،
آخر مجلد عمل، وحالة أي خطة قيد التنفيذ. يدعم:
- list   : عرض كل الجلسات المحفوظة.
- switch : تفعيل جلسة أخرى كجلسة "حالية" (تُستأنف تلقائيًا لاحقًا).
- resume : استرجاع تفاصيل جلسة سابقة والعودة للعمل فيها.
- archive: أرشفة جلسة قديمة (تُستبعد من القوائم الافتراضية لكن تظل محفوظة).
"""

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


class SessionManager:
    def __init__(self, base_dir: str = None, resume_id: Optional[str] = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai/sessions"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.current_pointer_path = self.base_dir / ".current"

        if resume_id:
            self.session_id = resume_id
            self.session_path = self.base_dir / f"{self.session_id}.json"
            self._data = self._load_existing() or self._new_session_data()
        else:
            self.session_id = str(uuid.uuid4())[:8]
            self.session_path = self.base_dir / f"{self.session_id}.json"
            self._data = self._new_session_data()

        self._save()
        self._set_current_pointer(self.session_id)

    def _new_session_data(self) -> Dict[str, Any]:
        return {
            "id": self.session_id,
            "started_at": time.time(),
            "ended_at": None,
            "cwd": os.getcwd(),
            "commands": [],
            "archived": False,
        }

    def _load_existing(self) -> Optional[Dict[str, Any]]:
        if not self.session_path.exists():
            return None
        try:
            with open(self.session_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    def _save(self) -> None:
        with open(self.session_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    def _set_current_pointer(self, session_id: str) -> None:
        self.current_pointer_path.write_text(session_id, encoding="utf-8")

    def record_command(self, command: str, success: bool = True) -> None:
        self._data["commands"].append({
            "ts": time.time(), "command": command, "success": success,
        })
        self._save()

    def end_session(self) -> None:
        self._data["ended_at"] = time.time()
        self._save()

    @classmethod
    def get_current_session_id(cls, base_dir: str = None) -> Optional[str]:
        base = Path(base_dir or os.path.expanduser("~/.cai/sessions"))
        pointer = base / ".current"
        if pointer.exists():
            return pointer.read_text(encoding="utf-8").strip()
        return None

    @classmethod
    def list_sessions(cls, base_dir: str = None, include_archived: bool = False) -> List[Dict[str, Any]]:
        base = Path(base_dir or os.path.expanduser("~/.cai/sessions"))
        sessions = []
        for f in sorted(base.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            try:
                with open(f, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                if data.get("archived") and not include_archived:
                    continue
                sessions.append(data)
            except (json.JSONDecodeError, OSError):
                continue
        return sessions

    @classmethod
    def load_session(cls, session_id: str, base_dir: str = None) -> Optional[Dict[str, Any]]:
        base = Path(base_dir or os.path.expanduser("~/.cai/sessions"))
        path = base / f"{session_id}.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def archive(cls, session_id: str, base_dir: str = None) -> bool:
        base = Path(base_dir or os.path.expanduser("~/.cai/sessions"))
        path = base / f"{session_id}.json"
        if not path.exists():
            return False
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["archived"] = True
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    @classmethod
    def unarchive(cls, session_id: str, base_dir: str = None) -> bool:
        base = Path(base_dir or os.path.expanduser("~/.cai/sessions"))
        path = base / f"{session_id}.json"
        if not path.exists():
            return False
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["archived"] = False
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True

    def summary(self) -> str:
        count = len(self._data["commands"])
        return f"Session {self.session_id} | بدأت: {time.ctime(self._data['started_at'])} | عدد الأوامر: {count}"

    @classmethod
    def render_list(cls, base_dir: str = None) -> str:
        sessions = cls.list_sessions(base_dir)
        current_id = cls.get_current_session_id(base_dir)
        if not sessions:
            return "لا توجد جلسات محفوظة."

        lines = ["الجلسات المحفوظة:"]
        for s in sessions:
            marker = "→" if s["id"] == current_id else " "
            started = time.strftime("%Y-%m-%d %H:%M", time.localtime(s["started_at"]))
            lines.append(f"  {marker} {s['id']}  |  {started}  |  {len(s['commands'])} أمر")
        return "\n".join(lines)

