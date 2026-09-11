"""
Storage Access Manager
------------------------
Termux معزول افتراضيًا عن تخزين الهاتف العام (Photos, Downloads,
WhatsApp Media...)، والوصول له محتاج المستخدم يشغّل termux-setup-storage
بنفسه (بيطلب إذن Android صريح ويعمل symlinks في ~/storage/).

هذا الملف لا "يمنح" الإذن (مستحيل برمجيًا من جوه Termux لأسباب أمنية
مقصودة من Android)، لكنه يكتشف هل الإذن اتاخد قبل كده، ويوجّه المستخدم
بوضوح لو لأ، ويوفر اختصارات آمنة للتنقل بين مجلدات التخزين الشائعة
بعد ما الإذن يتاخد.
"""

import os
from pathlib import Path
from typing import Dict, Optional

from cai.platform.platform_detector import PlatformInfo


class StorageAccessManager:
    def __init__(self, platform_info: PlatformInfo):
        self.platform_info = platform_info
        self.storage_root = platform_info.home_dir / "storage"

    def is_storage_setup(self) -> bool:
        return self.platform_info.is_termux and self.storage_root.exists()

    def known_shortcuts(self) -> Dict[str, Path]:
        """أشهر مجلدات التخزين المتاحة بعد termux-setup-storage."""
        if not self.is_storage_setup():
            return {}

        candidates = {
            "shared": self.storage_root / "shared",
            "downloads": self.storage_root / "downloads",
            "dcim": self.storage_root / "dcim",
            "pictures": self.storage_root / "pictures",
            "music": self.storage_root / "music",
            "movies": self.storage_root / "movies",
        }
        return {name: path for name, path in candidates.items() if path.exists()}

    def resolve_shortcut(self, name: str) -> Optional[Path]:
        return self.known_shortcuts().get(name.lower())

    def request_setup_instructions(self) -> str:
        return (
            "🔒 لسه مفيش وصول لتخزين الهاتف. الخطوات:\n"
            "  1. شغّل الأمر: termux-setup-storage\n"
            "  2. هيظهر طلب إذن من Android — اضغط 'Allow' / 'السماح'.\n"
            "  3. بعد كده هتلاقي مجلدات الهاتف متاحة تحت ~/storage/ "
            "(shared, downloads, dcim, pictures...).\n\n"
            "cai لا يقدر يمنح هذا الإذن برمجيًا لأسباب أمنية من نظام Android نفسه، "
            "لازم يتم يدويًا من المستخدم مرة واحدة فقط."
        )

    def list_projects_in_downloads(self, marker_files=("requirements.txt", "package.json", ".git")) -> list:
        """يبحث عن مشاريع برمجية محتملة داخل مجلد التنزيلات (سيناريو شائع جدًا في Termux)."""
        downloads = self.resolve_shortcut("downloads")
        if not downloads:
            return []

        found = []
        try:
            for entry in downloads.iterdir():
                if entry.is_dir() and any((entry / marker).exists() for marker in marker_files):
                    found.append(str(entry))
        except (OSError, PermissionError):
            pass
        return found

    def render_summary(self) -> str:
        if not self.platform_info.is_termux:
            return "هذه الميزة مخصصة لبيئة Termux فقط."

        if not self.is_storage_setup():
            return self.request_setup_instructions()

        shortcuts = self.known_shortcuts()
        lines = ["✅ الوصول لتخزين الهاتف متاح. المجلدات المكتشفة:"]
        for name, path in shortcuts.items():
            lines.append(f"  {name:<10} → {path}")

        projects = self.list_projects_in_downloads()
        if projects:
            lines.append("\n📁 مشاريع محتملة في Downloads:")
            lines.extend(f"  - {p}" for p in projects)

        return "\n".join(lines)
