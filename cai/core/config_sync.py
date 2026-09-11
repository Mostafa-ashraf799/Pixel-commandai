"""
Config Sync
-------------
مزامنة اختيارية للإعدادات (مش مفاتيح API — دي بتفضل محلية لكل جهاز لأسباب
أمان) بين الكمبيوتر والهاتف. الطريقة المستخدمة هنا بسيطة ومباشرة بدون
سيرفر مركزي: تصدير حزمة إعدادات (config + aliases + prompts المخصصة)
كملف JSON واحد، ونقله يدويًا (أو عبر أي أداة مزامنة ملفات المستخدم
بيفضّلها: Syncthing, rsync عبر SSH, Google Drive...) واستيراده على
الجهاز التاني.

بشكل متعمد لا يُزامن:
- مفاتيح API (~/.cai/keys.enc) — كل جهاز يضبط مفاتيحه بنفسه.
- Sessions/History/Memory — بيانات محلية بطبيعتها.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict


SYNCABLE_KEYS = [
    "provider", "model", "mode", "theme", "language",
    "monthly_budget_usd", "telemetry_enabled", "remote_ollama_url",
]


class ConfigSyncManager:
    def __init__(self, config, aliases_manager):
        self.config = config
        self.aliases = aliases_manager

    def export_bundle(self, output_path: str) -> str:
        bundle: Dict[str, Any] = {
            "exported_at": time.time(),
            "config": {k: self.config.get(k) for k in SYNCABLE_KEYS if self.config.get(k) is not None},
            "aliases": self.aliases.list_all(),
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(bundle, f, indent=2, ensure_ascii=False)

        return (
            f"تم تصدير حزمة الإعدادات إلى: {output_path}\n"
            f"انقلها للجهاز التاني (عبر Syncthing/Google Drive/scp) ثم استخدم:\n"
            f"  sync import {output_path}"
        )

    def import_bundle(self, input_path: str, overwrite: bool = True) -> str:
        path = Path(input_path)
        if not path.exists():
            return f"الملف غير موجود: {input_path}"

        try:
            with open(path, "r", encoding="utf-8") as f:
                bundle = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            return f"تعذّرت قراءة الملف: {e}"

        applied_config = 0
        for key, value in bundle.get("config", {}).items():
            if key in SYNCABLE_KEYS:
                self.config.set(key, value)
                applied_config += 1

        applied_aliases = 0
        for name, expansion in bundle.get("aliases", {}).items():
            self.aliases.add(name, expansion)
            applied_aliases += 1

        exported_at = bundle.get("exported_at")
        when = time.ctime(exported_at) if exported_at else "غير معروف"

        return (
            f"تم استيراد الإعدادات (مُصدَّرة في {when}):\n"
            f"  {applied_config} إعداد عام\n"
            f"  {applied_aliases} اختصار (alias)\n"
            f"ملاحظة: مفاتيح API لم تُستورد عمدًا؛ اضبطها يدويًا عبر 'api add' لكل جهاز."
        )
