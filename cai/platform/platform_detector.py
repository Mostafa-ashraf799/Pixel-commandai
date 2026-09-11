"""
Platform Detector
-------------------
يكتشف هل cai شغال داخل Termux (Android) أو نظام Linux/macOS/Windows
عادي، ويوفر المسارات والأوامر الصحيحة لكل بيئة.

الفروقات الجوهرية في Termux:
- مفيش sudo (المستخدم أصلاً بدون root في الحالة الافتراضية).
- مدير الحزم هو `pkg` (واجهة فوق apt خاصة بـ Termux)، مش apt مباشرة.
- المسار الجذر مختلف تمامًا: /data/data/com.termux/files/usr
- مجلد home: /data/data/com.termux/files/home
- الوصول لتخزين الهاتف (Photos, Downloads...) محتاج `termux-setup-storage`
  أولاً، وبعدها بيظهر عبر ~/storage/ (شامل shared, downloads, dcim...).
- أدوات الهاتف (بطارية، إشعارات، GPS، حافظة) متاحة فقط عبر Termux:API
  (حزمة منفصلة + تطبيق Termux:API مثبّت على الهاتف).
"""

import os
import platform
import shutil
from pathlib import Path
from typing import Optional


class PlatformInfo:
    def __init__(self):
        self.is_termux = self._detect_termux()
        self.os_name = "Termux (Android)" if self.is_termux else platform.system()

    def _detect_termux(self) -> bool:
        # أدق طريقة: متغير البيئة PREFIX اللي Termux بيضبطه دايمًا،
        # مع تأكيد إضافي من وجود مسار Termux المميز.
        prefix = os.environ.get("PREFIX", "")
        return "com.termux" in prefix or Path("/data/data/com.termux").exists()

    @property
    def home_dir(self) -> Path:
        return Path(os.path.expanduser("~"))

    @property
    def package_manager(self) -> str:
        if self.is_termux:
            return "pkg"
        if self.os_name == "Darwin":
            return "brew"
        if self.os_name == "Windows":
            return "winget"
        for mgr in ("apt", "dnf", "pacman"):
            if shutil.which(mgr):
                return mgr
        return "apt"

    @property
    def supports_sudo(self) -> bool:
        return not self.is_termux and self.os_name != "Windows"

    @property
    def storage_shared_dir(self) -> Optional[Path]:
        """مسار التخزين المشترك للهاتف بعد termux-setup-storage، أو None لو مش مفعّل."""
        if not self.is_termux:
            return None
        shared = self.home_dir / "storage" / "shared"
        return shared if shared.exists() else None

    @property
    def storage_downloads_dir(self) -> Optional[Path]:
        if not self.is_termux:
            return None
        downloads = self.home_dir / "storage" / "downloads"
        return downloads if downloads.exists() else None

    def has_termux_api(self) -> bool:
        """يتحقق من تثبيت أدوات Termux:API (الحزمة + غالبًا تطبيق Termux:API على الهاتف)."""
        return self.is_termux and shutil.which("termux-battery-status") is not None

    def storage_setup_hint(self) -> str:
        return (
            "الوصول لتخزين الهاتف (صور، تنزيلات...) يحتاج إذنًا أولاً. شغّل:\n"
            "  termux-setup-storage\n"
            "وافق على الإذن اللي هيظهر، وبعدها هتلاقي المجلدات متاحة في ~/storage/"
        )

    def termux_api_setup_hint(self) -> str:
        return (
            "أدوات الهاتف (بطارية، إشعارات، GPS، الحافظة) تحتاج:\n"
            "  1. تثبيت تطبيق Termux:API من نفس المصدر اللي ثبّت منه Termux (F-Droid غالبًا).\n"
            "  2. تشغيل: pkg install termux-api"
        )

    def summary(self) -> str:
        lines = [f"النظام: {self.os_name}"]
        if self.is_termux:
            lines.append(f"مدير الحزم: {self.package_manager} (بدون sudo)")
            lines.append(f"Termux:API: {'✅ متاح' if self.has_termux_api() else '❌ غير مثبّت'}")
            storage = self.storage_shared_dir
            lines.append(f"تخزين الهاتف: {'✅ متاح على ' + str(storage) if storage else '❌ غير مُعد (شغّل termux-setup-storage)'}")
        return "\n".join(lines)


# نسخة وحيدة يُعاد استخدامها في كل المشروع (Platform detection مكلفة نسبيًا لتكرارها)
_platform_info: Optional[PlatformInfo] = None


def get_platform_info() -> PlatformInfo:
    global _platform_info
    if _platform_info is None:
        _platform_info = PlatformInfo()
    return _platform_info
