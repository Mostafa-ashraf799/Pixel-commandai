"""
Offline Mode
--------------
لو الإنترنت مقطوع أو أي Provider سحابي (OpenAI, Gemini, ...) مش متاح،
النظام ده بيكتشف الحالة تلقائيًا ويقترح (أو يحوّل تلقائيًا لو مفعّل)
لاستخدام Ollama كموديل محلي بديل، عشان cai يفضل شغال حتى بدون نت.
"""

import socket
from typing import Optional

from cai.providers.provider_manager import ProviderManager


class OfflineModeManager:
    def __init__(self, provider_manager: ProviderManager, auto_switch: bool = False):
        self.provider_manager = provider_manager
        self.auto_switch = auto_switch
        self._last_online_state: Optional[bool] = None

    def is_internet_available(self, host: str = "8.8.8.8", port: int = 53, timeout: float = 2.0) -> bool:
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
            return True
        except OSError:
            return False

    def check_and_handle(self) -> Optional[str]:
        """
        يُستدعى دوريًا أو قبل أي طلب AI مهم. يرجع رسالة توضيحية لو حصل
        تحويل تلقائي للوضع Offline، أو None لو كل حاجة طبيعية.
        """
        online = self.is_internet_available()

        if online == self._last_online_state:
            return None  # مفيش تغيير في الحالة، مفيش داعي لأي إجراء

        self._last_online_state = online

        if not online:
            current_provider = self.provider_manager.status()["provider"]
            if current_provider == "ollama":
                return "⚠️ لا يوجد اتصال بالإنترنت، لكنك بالفعل تستخدم Ollama (محلي) — لا حاجة للتبديل."

            if self.auto_switch:
                switched = self.provider_manager.switch_provider("ollama")
                if switched:
                    return (
                        "🔌 تم اكتشاف انقطاع الإنترنت. تم التحويل تلقائيًا إلى Ollama (نموذج محلي)."
                    )
                return "🔌 انقطع الإنترنت، وفشل التحويل التلقائي لـ Ollama (تأكد أنه مثبّت ومشغّل)."

            return (
                "🔌 تم اكتشاف انقطاع الإنترنت. استخدم 'provider ollama' للتحويل لنموذج محلي، "
                "أو 'cfg auto_offline_switch true' لتفعيل التحويل التلقائي مستقبلاً."
            )

        return "🌐 عاد الاتصال بالإنترنت."
