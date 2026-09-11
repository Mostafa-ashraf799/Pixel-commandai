"""
Provider Manager
----------------
نقطة الدخول الوحيدة لباقي البرنامج للتعامل مع أي AI Provider.
مسؤول عن:
- تحميل الـ Provider الحالي حسب الإعدادات.
- تبديل الـ Provider/الموديل وقت التشغيل (أمر mdl / provider).
- توفير واجهة chat() واحدة موحدة.
"""

from typing import List, Optional

from cai.config.config_manager import ConfigManager
from cai.security.api_key_manager import APIKeyManager
from cai.providers.base_provider import BaseProvider, ChatMessage, ProviderResponse
from cai.providers.adapters.openai_compatible import OpenAICompatibleProvider
from cai.providers.adapters.gemini_provider import GeminiProvider
from cai.providers.adapters.ollama_provider import OllamaProvider
from cai.providers.ollama_connector import OllamaConnector
from cai.cloud.pixel_provider import PixelProvider
from cai.cloud.auth_manager import AuthManager

# TODO: replace with your real Supabase project URL + anon key before shipping.
# These two values are safe to ship in the client — they are NOT secret.
# The OpenRouter key stays server-side only, inside the chat-proxy Edge Function.
PIXEL_SUPABASE_URL = "https://fazjxaukksdkeztejeow.supabase.co"
PIXEL_SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZhemp4YXVra3Nka2V6dGVqZW93Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODg2MjI3NTQsImV4cCI6MjEwNDE5ODc1NH0.JBG5Va1EmbbXLa7VMPrMMSqB5IN4BU67iMb5ZDhz3FI"


OPENAI_COMPATIBLE = {"openai", "groq", "openrouter", "deepseek"}


class ProviderManager:
    def __init__(self, config: ConfigManager, keys: APIKeyManager, cost_tracker=None):
        self.config = config
        self.keys = keys
        self.cost_tracker = cost_tracker  # اختياري، يُضبط لاحقًا عبر attach_cost_tracker لتفادي circular imports
        self.ollama_connector = OllamaConnector(config)
        # Shared across the whole app so login persists across a single run
        # and so command_router can reuse it for `login`/`logout`/`whoami` commands.
        self.pixel_auth = AuthManager(PIXEL_SUPABASE_URL, PIXEL_SUPABASE_ANON_KEY)
        self._provider: Optional[BaseProvider] = None
        self.reload()

    def attach_cost_tracker(self, cost_tracker) -> None:
        self.cost_tracker = cost_tracker

    def _build_provider(self, provider_name: str) -> BaseProvider:
        provider_name = provider_name.lower()
        api_key = self.keys.get_key(provider_name)

        if provider_name in OPENAI_COMPATIBLE:
            return OpenAICompatibleProvider(provider_name, api_key=api_key)
        if provider_name == "gemini":
            return GeminiProvider(api_key=api_key)
        if provider_name == "ollama":
            # يكتشف تلقائيًا: محلي أولاً، وإلا عنوان بعيد محفوظ (مفيد جدًا من الهاتف)
            discovered_url = self.ollama_connector.discover()
            base_url = discovered_url or "http://localhost:11434"
            return OllamaProvider(api_key=api_key, base_url=base_url)
        if provider_name == "pixel":
            # Pixel CommandAI cloud provider — no local API key involved.
            # Auth is handled separately via `pixel-cai login`.
            return PixelProvider(PIXEL_SUPABASE_URL, self.pixel_auth)

        raise ValueError(f"Provider غير مدعوم: {provider_name}")

    def reload(self) -> None:
        provider_name = self.config.get("provider", "openrouter")
        self._provider = self._build_provider(provider_name)

    @property
    def current(self) -> BaseProvider:
        return self._provider

    def switch_provider(self, provider_name: str) -> bool:
        try:
            new_provider = self._build_provider(provider_name)
        except ValueError:
            return False
        self._provider = new_provider
        self.config.set("provider", provider_name.lower())
        return True

    def switch_model(self, model_name: str) -> None:
        self.config.set("model", model_name)

    def chat(self, messages: List[ChatMessage], **kwargs) -> ProviderResponse:
        model = kwargs.pop("model", None) or self.config.get("model")
        if not self._provider.is_configured():
            return ProviderResponse(
                content="",
                error=(
                    f"لا يوجد API key مضبوط لـ {self._provider.name}. "
                    f"استخدم أمر `api add {self._provider.name}` لإضافته."
                ),
            )
        response = self._provider.chat(messages, model=model, **kwargs)

        if response.ok and self.cost_tracker and response.usage:
            prompt_tokens = response.usage.get("prompt_tokens", 0)
            completion_tokens = response.usage.get("completion_tokens", 0)
            if prompt_tokens or completion_tokens:
                self.cost_tracker.record(
                    provider=self._provider.name,
                    model=response.model or model or "unknown",
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                )

        return response

    def test_current(self) -> bool:
        if not self._provider.is_configured():
            return False
        return self._provider.test_connection()

    def status(self) -> dict:
        return {
            "provider": self._provider.name,
            "model": self.config.get("model"),
            "configured": self._provider.is_configured(),
        }
