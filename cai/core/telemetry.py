"""
Telemetry (Opt-in/Opt-out)
-----------------------------
نظام تجميع إحصائيات استخدام مجهولة الهوية بالكامل (عدد الأوامر، الأدوات
الأكثر استخدامًا) لأغراض تحسين cai مستقبلاً — لكنه اختياري تمامًا ومعطّل
افتراضيًا. المستخدم يفعّله بوعي، ويقدر يقفله في أي وقت، وكل البيانات
تُخزَّن محليًا فقط (لا يوجد إرسال فعلي لأي سيرفر في هذا الكود الأساسي؛
أي تفعيل لإرسال بيانات فعلي لازم يكون صريح ومفصل في التوثيق).
"""

import json
import os
import time
from collections import Counter
from pathlib import Path
from typing import Dict


class TelemetryManager:
    def __init__(self, base_dir: str = None, enabled: bool = False):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.telemetry_path = self.base_dir / "telemetry.json"
        self.enabled = enabled

    def set_enabled(self, enabled: bool) -> str:
        self.enabled = enabled
        status = "تم تفعيل" if enabled else "تم إيقاف"
        return f"{status} جمع الإحصائيات المجهولة (Telemetry). البيانات تُحفظ محليًا فقط ولا تُرسل لأي مكان."

    def record_command_usage(self, command_word: str) -> None:
        if not self.enabled:
            return

        data = self._load()
        data.setdefault("command_counts", {})
        data["command_counts"][command_word] = data["command_counts"].get(command_word, 0) + 1
        data["last_updated"] = time.time()
        self._save(data)

    def _load(self) -> Dict:
        if not self.telemetry_path.exists():
            return {"command_counts": {}, "created_at": time.time()}
        try:
            with open(self.telemetry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {"command_counts": {}, "created_at": time.time()}

    def _save(self, data: Dict) -> None:
        with open(self.telemetry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def export_local_report(self) -> str:
        """يعرض للمستخدم بالضبط البيانات المحفوظة عنه (شفافية كاملة)."""
        if not self.enabled:
            return "Telemetry غير مفعّل حاليًا. لا توجد بيانات مجمّعة."

        data = self._load()
        counts = Counter(data.get("command_counts", {}))
        if not counts:
            return "لا توجد بيانات استخدام مسجّلة بعد."

        lines = ["أكثر الأوامر استخدامًا (بيانات محلية بالكامل، غير مُرسَلة لأي سيرفر):"]
        for cmd, count in counts.most_common(10):
            lines.append(f"  {cmd:<15} {count} مرة")
        return "\n".join(lines)

    def clear_data(self) -> str:
        if self.telemetry_path.exists():
            self.telemetry_path.unlink()
        return "تم حذف كل بيانات Telemetry المحلية."
