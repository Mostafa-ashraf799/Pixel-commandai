"""
Bootstrap
---------
نقطة تجميع واحدة تسجّل كل خدمات cai في الـ DI Container، بالترتيب الصحيح
للاعتماديات (Config قبل Logger، Logger قبل Provider، إلخ).

بعد الاستدعاء، أي جزء من البرنامج بيقدر يجيب أي خدمة عبر:
    container.resolve("config")
    container.resolve("event_bus")
    container.resolve("providers")

من غير ما يعرف تفاصيل إزاي اتبنت.
"""

from cai.core.di.container import Container
from cai.core.events.event_bus import EventBus
from cai.config.config_manager import ConfigManager
from cai.security.api_key_manager import APIKeyManager
from cai.security.permission_manager import PermissionManager
from cai.providers.provider_manager import ProviderManager
from cai.engine.execution_engine import ExecutionEngine
from cai.memory.memory_manager import MemoryManager
from cai.memory.history_manager import HistoryManager
from cai.memory.session_manager import SessionManager
from cai.core.cost_tracker import CostTracker
from cai.utils.logger import get_logger


def build_container() -> Container:
    container = Container()

    # ---------- خدمات أساسية بدون اعتماديات ----------
    container.register_singleton("event_bus", lambda c: EventBus())
    container.register_singleton("config", lambda c: ConfigManager())
    container.register_singleton("logger", lambda c: get_logger(c.resolve("config").get("log_level", "info")))
    container.register_singleton("keys", lambda c: APIKeyManager())

    # ---------- خدمات تعتمد على config ----------
    container.register_singleton(
        "permissions",
        lambda c: PermissionManager(mode=c.resolve("config").get("mode", "smart")),
    )
    container.register_singleton(
        "cost_tracker",
        lambda c: CostTracker(monthly_budget_usd=c.resolve("config").get("monthly_budget_usd")),
    )
    container.register_singleton(
        "history",
        lambda c: HistoryManager(limit=c.resolve("config").get("history_limit", 500)),
    )
    container.register_singleton("memory", lambda c: MemoryManager())
    container.register_singleton("session", lambda c: SessionManager())

    # ---------- خدمات مترابطة (provider + engine) ----------
    def _build_providers(c: Container) -> ProviderManager:
        pm = ProviderManager(c.resolve("config"), c.resolve("keys"))
        pm.attach_cost_tracker(c.resolve("cost_tracker"))
        return pm

    container.register_singleton("providers", _build_providers)

    def _build_engine(c: Container) -> ExecutionEngine:
        # confirm_callback يُضبط لاحقًا من الـ UI Layer (Shell) لأنه يحتاج input() تفاعلي
        return ExecutionEngine(c.resolve("permissions"))

    container.register_singleton("engine", _build_engine)

    return container
