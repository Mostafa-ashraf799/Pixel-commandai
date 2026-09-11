"""
Permission Manager
-------------------
يصنّف أي أمر نظام قبل تنفيذه إلى:
- SAFE       : تنفيذ مباشر بدون سؤال.
- WARNING    : تنفيذ مع تنبيه (وسؤال في وضع Safe/Smart).
- DANGEROUS  : يطلب تأكيد المستخدم دائمًا.
- CRITICAL   : يطلب تأكيد صريح مضاعف (كتابة "yes" كاملة) دائمًا،
               بغض النظر عن الوضع.

هذا الملف هو خط الدفاع الأول قبل أي execution فعلي على جهاز المستخدم.
"""

import re
from enum import Enum
from typing import List, Tuple


class RiskLevel(Enum):
    SAFE = "safe"
    WARNING = "warning"
    DANGEROUS = "dangerous"
    CRITICAL = "critical"


# أنماط أوامر معروفة الخطورة (regex بسيطة، قابلة للتوسيع)
CRITICAL_PATTERNS = [
    r"\brm\s+-rf\s+/(\s|$)",
    r"\bmkfs\b",
    r"\bdd\s+if=.*of=/dev/",
    r":\(\)\s*\{\s*:\|:&\s*\};:",      # fork bomb
    r"\bshutdown\b",
    r"\breboot\b",
    r">\s*/dev/sd[a-z]",
    r"\bformat\s+[a-zA-Z]:",          # Windows format C:
]

DANGEROUS_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\brm\s+-r\b",
    r"\bdel\s+/s\b",
    r"\bDrop-?\s*Database\b",
    r"\bchmod\s+-R\s+777\b",
    r"\bchown\s+-R\b",
    r"\bkill\s+-9\b",
    r"\bgit\s+push\s+--force\b",
    r"\bdocker\s+system\s+prune\s+-a\b",
    r"\btruncate\s+table\b",
]

WARNING_PATTERNS = [
    r"\bsudo\b",
    r"\bapt(-get)?\s+remove\b",
    r"\bapt(-get)?\s+purge\b",
    r"\bpip\s+uninstall\b",
    r"\bnpm\s+uninstall\b",
    r"\bgit\s+reset\s+--hard\b",
    r"\bgit\s+checkout\s+--\s+\.\b",
    r"\bmv\b.*\s+/",
]


class PermissionManager:
    def __init__(self, mode: str = "smart"):
        self.mode = mode  # safe | smart | expert

    def classify(self, command: str) -> RiskLevel:
        cmd = command.strip()

        for pattern in CRITICAL_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                return RiskLevel.CRITICAL

        for pattern in DANGEROUS_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                return RiskLevel.DANGEROUS

        for pattern in WARNING_PATTERNS:
            if re.search(pattern, cmd, re.IGNORECASE):
                return RiskLevel.WARNING

        return RiskLevel.SAFE

    def requires_confirmation(self, command: str) -> Tuple[bool, RiskLevel]:
        """يقرر هل الأمر محتاج تأكيد المستخدم حسب الخطورة ووضع التشغيل الحالي."""
        risk = self.classify(command)

        if risk == RiskLevel.CRITICAL:
            return True, risk
        if risk == RiskLevel.DANGEROUS:
            return True, risk
        if risk == RiskLevel.WARNING:
            return self.mode in ("safe", "smart"), risk
        # SAFE
        return self.mode == "safe" and False, risk  # الأوامر الآمنة لا تحتاج تأكيد حتى في safe

    def explain_risk(self, risk: RiskLevel) -> str:
        explanations = {
            RiskLevel.SAFE: "أمر آمن.",
            RiskLevel.WARNING: "⚠️ هذا الأمر قد يغيّر أشياء مهمة، يُفضّل الانتباه.",
            RiskLevel.DANGEROUS: "🚨 هذا الأمر خطير وقد يحذف/يعدّل بيانات لا يمكن استرجاعها.",
            RiskLevel.CRITICAL: "🛑 هذا الأمر حرج جدًا وقد يضر النظام بالكامل!",
        }
        return explanations[risk]

    def set_mode(self, mode: str) -> None:
        if mode in ("safe", "smart", "expert"):
            self.mode = mode
