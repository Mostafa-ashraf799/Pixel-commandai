"""
Layered Configuration
------------------------
بدل ملف config.json واحد عام، النظام ده بيدعم 4 طبقات بترتيب أولوية
(الأعلى بيغلب الأقل):

    Session   (مؤقت لهذه الجلسة فقط، لا يُحفظ على القرص)
    Workspace (مجلد .cai/workspace.json داخل مجلد العمل الحالي)
    Project   (ملف .cai.json في جذر المشروع الحالي، يُشارك مع الفريق عبر Git)
    Global    (~/.cai/config.json، الإعدادات الافتراضية للمستخدم على الجهاز)

القيمة الفعلية لأي مفتاح = أول طبقة (من الأعلى للأسفل) فيها هذا المفتاح.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class LayeredConfig:
    LAYER_ORDER = ["session", "workspace", "project", "global"]

    def __init__(self, global_config, project_root: str = "."):
        self.global_config = global_config  # نسخة ConfigManager الحالية (تبقى كما هي كطبقة global)
        self.project_root = Path(project_root).resolve()

        self.project_path = self.project_root / ".cai.json"
        self.workspace_path = self.project_root / ".cai" / "workspace.json"

        self._session_overrides: Dict[str, Any] = {}
        self._project_data: Dict[str, Any] = self._load_json(self.project_path)
        self._workspace_data: Dict[str, Any] = self._load_json(self.workspace_path)

    def _load_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_json(self, path: Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get(self, key: str, default: Any = None) -> Any:
        if key in self._session_overrides:
            return self._session_overrides[key]
        if key in self._workspace_data:
            return self._workspace_data[key]
        if key in self._project_data:
            return self._project_data[key]
        return self.global_config.get(key, default)

    def set(self, key: str, value: Any, layer: str = "session") -> str:
        if layer == "session":
            self._session_overrides[key] = value
        elif layer == "workspace":
            self._workspace_data[key] = value
            self._save_json(self.workspace_path, self._workspace_data)
        elif layer == "project":
            self._project_data[key] = value
            self._save_json(self.project_path, self._project_data)
        elif layer == "global":
            self.global_config.set(key, value)
        else:
            return f"طبقة غير معروفة: {layer}. الطبقات المتاحة: {', '.join(self.LAYER_ORDER)}"

        return f"تم ضبط {key}={value} في طبقة {layer}."

    def explain(self, key: str) -> str:
        """يوضح من أي طبقة جاءت القيمة الحالية لمفتاح معين (مفيد لتتبع مصدر إعداد)."""
        if key in self._session_overrides:
            return f"{key} = {self._session_overrides[key]}  (من: session)"
        if key in self._workspace_data:
            return f"{key} = {self._workspace_data[key]}  (من: workspace)"
        if key in self._project_data:
            return f"{key} = {self._project_data[key]}  (من: project)"
        global_value = self.global_config.get(key)
        if global_value is not None:
            return f"{key} = {global_value}  (من: global)"
        return f"{key} غير مضبوط في أي طبقة."

    def all_merged(self) -> Dict[str, Any]:
        """يرجع كل الإعدادات مدمجة حسب أولوية الطبقات."""
        merged = dict(self.global_config.all())
        merged.update(self._project_data)
        merged.update(self._workspace_data)
        merged.update(self._session_overrides)
        return merged

    def render_layers(self) -> str:
        lines = ["طبقات الإعدادات (من الأعلى أولوية للأقل):"]
        lines.append(f"  session   ({len(self._session_overrides)} مفتاح مؤقت)")
        lines.append(f"  workspace ({len(self._workspace_data)} مفتاح) — {self.workspace_path}")
        lines.append(f"  project   ({len(self._project_data)} مفتاح) — {self.project_path}")
        lines.append(f"  global    ({len(self.global_config.all())} مفتاح) — {self.global_config.config_path}")
        return "\n".join(lines)
