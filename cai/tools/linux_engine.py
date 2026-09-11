"""
Linux Engine
------------
وظائف مخصصة لأنظمة Linux: شرح الأوامر والـ flags، تحليل الأخطاء،
وإصلاح مشاكل شائعة (apt المعطل، بيئة Python، مشاكل الشبكة).
يعتمد على الـ AI للشرح، وعلى قواعد ثابتة لبعض الإصلاحات السريعة والمعروفة.
"""

from typing import Optional

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage
from cai.engine.execution_engine import ExecutionEngine, ExecutionResult


KNOWN_FIXES = {
    "dpkg was interrupted": "sudo dpkg --configure -a",
    "unable to lock the administration directory": "sudo rm /var/lib/dpkg/lock-frontend && sudo dpkg --configure -a",
    "could not get lock /var/lib/apt/lists": "sudo rm /var/lib/apt/lists/lock && sudo apt update",
    "externally-managed-environment": "استخدم: pip install <package> --break-system-packages، أو أنشئ virtualenv.",
}


class LinuxEngine:
    def __init__(self, provider_manager: ProviderManager, engine: ExecutionEngine):
        self.provider_manager = provider_manager
        self.engine = engine

    def explain_command(self, command: str) -> str:
        messages = [
            ChatMessage(
                role="system",
                content="أنت خبير Linux. اشرح الأمر التالي بالتفصيل، بما في ذلك كل flag مستخدم فيه، بشكل مبسط.",
            ),
            ChatMessage(role="user", content=command),
        ]
        response = self.provider_manager.chat(messages, temperature=0.2, max_tokens=800)
        return response.content if response.ok else f"❌ خطأ: {response.error}"

    def quick_fix_lookup(self, error_message: str) -> Optional[str]:
        """يبحث عن حل جاهز معروف قبل اللجوء للـ AI (أسرع وأرخص)."""
        lowered = error_message.lower()
        for key, fix in KNOWN_FIXES.items():
            if key in lowered:
                return fix
        return None

    def diagnose_and_fix(self, error_message: str, auto_run: bool = False) -> str:
        quick_fix = self.quick_fix_lookup(error_message)
        if quick_fix:
            if auto_run and not quick_fix.startswith("استخدم"):
                result: ExecutionResult = self.engine.run(quick_fix)
                return f"تم تطبيق إصلاح معروف: {quick_fix}\n{self.engine.analyze_result(result)}"
            return f"إصلاح مقترح (معروف): {quick_fix}"

        messages = [
            ChatMessage(
                role="system",
                content="أنت خبير Linux. حلل رسالة الخطأ التالية واقترح أمر إصلاح واحد محدد ودقيق.",
            ),
            ChatMessage(role="user", content=error_message),
        ]
        response = self.provider_manager.chat(messages, temperature=0.2, max_tokens=400)
        return response.content if response.ok else f"❌ خطأ: {response.error}"

    def diagnose_system(self) -> ExecutionResult:
        """تشخيص عام سريع للنظام."""
        cmd = (
            "echo '--- OS ---' && cat /etc/os-release 2>/dev/null | head -5; "
            "echo '--- Disk ---' && df -h /; "
            "echo '--- Memory ---' && free -h"
        )
        return self.engine.run(cmd)
