"""
Update System
--------------
يفحص وجود إصدار أحدث من cai عبر PyPI (لو نُشر مستقبلاً)، ويسمح بتحديث
الحزمة تلقائيًا، مع دعم Rollback فوري لو التحديث الجديد فيه مشكلة —
بيحتفظ بالإصدار السابق قبل أي ترقية عشان يقدر يرجعله بأمر واحد.
"""

from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    requests = None

from cai.engine.execution_engine import ExecutionEngine


class UpdateSystem:
    PACKAGE_NAME = "commandai"

    def __init__(self, current_version: str, engine: Optional[ExecutionEngine] = None, base_dir: str = None):
        import os
        self.current_version = current_version
        self.engine = engine
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.version_history_path = self.base_dir / "version_history.json"

    def check_latest_version(self) -> Optional[str]:
        if requests is None:
            return None
        try:
            resp = requests.get(f"https://pypi.org/pypi/{self.PACKAGE_NAME}/json", timeout=10)
            if resp.status_code != 200:
                return None
            return resp.json()["info"]["version"]
        except Exception:
            return None

    def is_update_available(self) -> Optional[bool]:
        latest = self.check_latest_version()
        if latest is None:
            return None
        return latest != self.current_version

    def _record_version_history(self, version: str) -> None:
        import json
        import time
        history = []
        if self.version_history_path.exists():
            try:
                with open(self.version_history_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except (json.JSONDecodeError, OSError):
                history = []
        history.append({"version": version, "ts": time.time()})
        history = history[-10:]  # الاحتفاظ بآخر 10 إصدارات بس
        with open(self.version_history_path, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2)

    def update(self) -> str:
        if not self.engine:
            return "لا يمكن التحديث: ExecutionEngine غير متاح."

        self._record_version_history(self.current_version)  # نحفظ الإصدار الحالي قبل الترقية

        result = self.engine.run(f"pip install --upgrade {self.PACKAGE_NAME}")
        if result.success:
            return "تم التحديث بنجاح ✅ (لو حصلت مشكلة، استخدم أمر: update rollback)"
        return f"فشل التحديث:\n{result.stderr}"

    def rollback(self) -> str:
        import json
        if not self.engine:
            return "لا يمكن التراجع: ExecutionEngine غير متاح."
        if not self.version_history_path.exists():
            return "لا يوجد سجل إصدارات سابقة للتراجع إليه."

        try:
            with open(self.version_history_path, "r", encoding="utf-8") as f:
                history = json.load(f)
        except (json.JSONDecodeError, OSError):
            return "تعذّرت قراءة سجل الإصدارات."

        if not history:
            return "لا يوجد إصدار سابق مسجّل."

        previous_version = history[-1]["version"]
        result = self.engine.run(f"pip install {self.PACKAGE_NAME}=={previous_version}")
        if result.success:
            history.pop()
            with open(self.version_history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
            return f"تم التراجع بنجاح إلى الإصدار {previous_version} ✅"
        return f"فشل التراجع:\n{result.stderr}"
