"""
Windows Engine
--------------
وظائف مخصصة لأنظمة Windows: PowerShell, CMD, Winget, وإدارة الخدمات
(Windows Services). Chocolatey مذكور كتوسعة مستقبلية اختيارية.
"""

from typing import Optional

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage
from cai.engine.execution_engine import ExecutionEngine, ExecutionResult


class WindowsEngine:
    def __init__(self, provider_manager: ProviderManager, engine: ExecutionEngine):
        self.provider_manager = provider_manager
        self.engine = engine

    def explain_command(self, command: str) -> str:
        messages = [
            ChatMessage(
                role="system",
                content="أنت خبير PowerShell وCMD. اشرح الأمر التالي بالتفصيل مع كل معامل مستخدم فيه.",
            ),
            ChatMessage(role="user", content=command),
        ]
        response = self.provider_manager.chat(messages, temperature=0.2, max_tokens=800)
        return response.content if response.ok else f"❌ خطأ: {response.error}"

    def list_services(self) -> ExecutionResult:
        return self.engine.run("Get-Service | Sort-Object Status -Descending")

    def start_service(self, service_name: str) -> ExecutionResult:
        return self.engine.run(f"Start-Service -Name '{service_name}'")

    def stop_service(self, service_name: str) -> ExecutionResult:
        return self.engine.run(f"Stop-Service -Name '{service_name}'")

    def winget_search(self, query: str) -> ExecutionResult:
        return self.engine.run(f"winget search {query}")

    def winget_install(self, package: str) -> ExecutionResult:
        return self.engine.run(f"winget install --id {package} -e")

    def system_info(self) -> ExecutionResult:
        return self.engine.run("systeminfo | findstr /C:\"OS\" /C:\"Memory\"")

    def diagnose_and_fix(self, error_message: str) -> str:
        messages = [
            ChatMessage(
                role="system",
                content="أنت خبير Windows/PowerShell. حلل رسالة الخطأ التالية واقترح أمر إصلاح واحد محدد.",
            ),
            ChatMessage(role="user", content=error_message),
        ]
        response = self.provider_manager.chat(messages, temperature=0.2, max_tokens=400)
        return response.content if response.ok else f"❌ خطأ: {response.error}"
