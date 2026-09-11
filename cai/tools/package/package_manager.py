"""
Package Manager (Cross-Platform)
---------------------------------
طبقة توافق موحدة فوق مدراء الحزم المختلفة:
apt, dnf, pacman, winget, brew, pip, npm, cargo.

الهدف: المستخدم يقول "install python" أو الـ AI يقرر تنفيذها،
والطبقة دي تختار الأمر الصحيح حسب نظام التشغيل المكتشف تلقائيًا،
أو حسب مدير حزم محدد صراحة (pip/npm/cargo مستقلين عن نظام التشغيل).
"""

import platform
import shutil
from typing import Optional

from cai.engine.execution_engine import ExecutionEngine, ExecutionResult
from cai.platform.platform_detector import get_platform_info


class PackageManager:
    SYSTEM_MANAGERS = {
        "apt": {"install": "sudo apt install -y {pkg}", "remove": "sudo apt remove -y {pkg}",
                "update": "sudo apt update", "upgrade": "sudo apt upgrade -y"},
        "dnf": {"install": "sudo dnf install -y {pkg}", "remove": "sudo dnf remove -y {pkg}",
                "update": "sudo dnf check-update", "upgrade": "sudo dnf upgrade -y"},
        "pacman": {"install": "sudo pacman -S --noconfirm {pkg}", "remove": "sudo pacman -R --noconfirm {pkg}",
                   "update": "sudo pacman -Sy", "upgrade": "sudo pacman -Syu --noconfirm"},
        "winget": {"install": "winget install {pkg}", "remove": "winget uninstall {pkg}",
                   "update": "winget upgrade --all", "upgrade": "winget upgrade --all"},
        "brew": {"install": "brew install {pkg}", "remove": "brew uninstall {pkg}",
                 "update": "brew update", "upgrade": "brew upgrade"},
        # Termux: pkg هو واجهة apt خاصة به، وبدون sudo لأن المستخدم أصلاً بدون root
        "pkg": {"install": "pkg install -y {pkg}", "remove": "pkg uninstall -y {pkg}",
                "update": "pkg update -y", "upgrade": "pkg upgrade -y"},
    }

    LANGUAGE_MANAGERS = {
        "pip": {"install": "pip install {pkg}", "remove": "pip uninstall -y {pkg}"},
        "npm": {"install": "npm install -g {pkg}", "remove": "npm uninstall -g {pkg}"},
        "cargo": {"install": "cargo install {pkg}", "remove": "cargo uninstall {pkg}"},
    }

    def __init__(self, engine: ExecutionEngine):
        self.engine = engine
        self.platform_info = get_platform_info()
        self.os_name = self.platform_info.os_name
        self.system_manager = self._detect_system_manager()

    def _detect_system_manager(self) -> Optional[str]:
        if self.platform_info.is_termux:
            return "pkg"
        if platform.system() == "Windows":
            return "winget" if shutil.which("winget") else None
        if platform.system() == "Darwin":
            return "brew" if shutil.which("brew") else None
        # Linux: نجرب بالترتيب الأكثر شيوعًا
        for manager in ("apt", "dnf", "pacman"):
            if shutil.which(manager):
                return manager
        return None

    def install(self, package: str, manager: Optional[str] = None) -> ExecutionResult:
        manager = manager or self.system_manager
        if not manager:
            return ExecutionResult(
                command=f"install {package}", stdout="", stderr="لم يتم العثور على مدير حزم مناسب لنظامك.",
                exit_code=-1, success=False, risk=None,
            )
        table = self.LANGUAGE_MANAGERS.get(manager) or self.SYSTEM_MANAGERS.get(manager)
        if not table:
            return ExecutionResult(
                command=f"install {package}", stdout="", stderr=f"مدير الحزم '{manager}' غير مدعوم.",
                exit_code=-1, success=False, risk=None,
            )
        cmd = table["install"].format(pkg=package)
        return self.engine.run(cmd)

    def remove(self, package: str, manager: Optional[str] = None) -> ExecutionResult:
        manager = manager or self.system_manager
        table = self.LANGUAGE_MANAGERS.get(manager) or self.SYSTEM_MANAGERS.get(manager, {})
        cmd = table.get("remove", "").format(pkg=package)
        if not cmd:
            return ExecutionResult(
                command=f"remove {package}", stdout="", stderr="مدير الحزم غير مدعوم لهذه العملية.",
                exit_code=-1, success=False, risk=None,
            )
        return self.engine.run(cmd)

    def update_index(self, manager: Optional[str] = None) -> ExecutionResult:
        manager = manager or self.system_manager
        table = self.SYSTEM_MANAGERS.get(manager, {})
        cmd = table.get("update")
        if not cmd:
            return ExecutionResult(
                command="update", stdout="", stderr="غير مدعوم لهذا المدير.",
                exit_code=-1, success=False, risk=None,
            )
        return self.engine.run(cmd)

    def upgrade_all(self, manager: Optional[str] = None) -> ExecutionResult:
        manager = manager or self.system_manager
        table = self.SYSTEM_MANAGERS.get(manager, {})
        cmd = table.get("upgrade")
        if not cmd:
            return ExecutionResult(
                command="upgrade", stdout="", stderr="غير مدعوم لهذا المدير.",
                exit_code=-1, success=False, risk=None,
            )
        return self.engine.run(cmd)

    def detect_best_manager_for(self, package_hint: str) -> str:
        """تخمين بسيط لمدير الحزم الأنسب بناءً على اسم الحزمة (يمكن للـ AI تجاوزه)."""
        hint = package_hint.lower()
        if hint.startswith("python-") or hint in ("flask", "django", "requests", "numpy", "pandas"):
            return "pip"
        if hint.startswith("node-") or hint in ("react", "vue", "typescript", "eslint"):
            return "npm"
        return self.system_manager or "apt"
