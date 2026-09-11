"""
Pixel Provider (Pixel CommandAI)
---------------------------------
Provider جديد يطبّق نفس واجهة BaseProvider، لكنه بدل ما يتصل بأي
AI API مباشرة، بيبعت الطلب لـ Edge Function على Supabase
(`chat-proxy`) اللي هي الوحيدة اللي شايلة مفتاح OpenRouter الحقيقي.

المستخدم النهائي محتاج بس يعمل تسجيل دخول (AuthManager) —
مفيش أي مفتاح API يتحط على جهازه أبدًا، والموديل الفعلي المستخدم
مش بيظهر له في أي رسالة أو خطأ.
"""

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional

from cai.providers.base_provider import BaseProvider, ChatMessage, ProviderResponse
from cai.cloud.auth_manager import AuthManager, AuthError


class QuotaExceededError(Exception):
    def __init__(self, message: str, window_end: Optional[str] = None):
        super().__init__(message)
        self.window_end = window_end


class PixelProvider(BaseProvider):
    name = "pixel"
    default_model = ""  # intentionally blank — the model is an internal server detail

    def __init__(self, supabase_url: str, auth_manager: AuthManager, **kwargs):
        super().__init__(api_key=None, **kwargs)
        self.supabase_url = supabase_url.rstrip("/")
        self.auth = auth_manager
        self.function_url = f"{self.supabase_url}/functions/v1/chat-proxy"

    def is_configured(self) -> bool:
        return self.auth.is_logged_in()

    def _messages_to_payload(self, messages: List[ChatMessage]) -> List[Dict[str, str]]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,   # ignored on purpose — server decides the model
        temperature: float = 0.4,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        command: Optional[str] = None,
        **kwargs,
    ) -> ProviderResponse:
        if not self.is_configured():
            return ProviderResponse(
                content="",
                error="لم يتم تسجيل الدخول. استخدم `pixel-cai login` أولاً.",
            )

        try:
            token = self.auth.get_access_token()
        except AuthError as e:
            return ProviderResponse(content="", error=str(e))

        body = {
            "messages": self._messages_to_payload(messages),
            "command": command,
            "extra": {
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        }

        req = urllib.request.Request(
            self.function_url,
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="ignore")
            try:
                parsed = json.loads(raw)
            except Exception:
                parsed = {"error": "unknown_error", "message": raw}

            if e.code == 429:
                return ProviderResponse(
                    content="",
                    error="انتهت حصتك الحالية من الاستخدام. هتتجدد تلقائيًا — جرب بعد شوية أو رقّي خطتك.",
                )
            if e.code == 401:
                return ProviderResponse(content="", error="انتهت الجلسة. سجّل الدخول مرة أخرى.")
            return ProviderResponse(content="", error=f"خطأ من الخادم: {parsed.get('message', parsed)}")
        except Exception as e:
            return ProviderResponse(content="", error=f"تعذر الاتصال بالخادم: {e}")

        content = data.get("content", "")
        warning = data.get("warning")
        if warning:
            content = f"{content}\n\n\u26a0\ufe0f {warning}"

        return ProviderResponse(
            content=content,
            model=None,  # never surfaced to the end user
            usage=data.get("usage", {}),
        )

    def test_connection(self) -> bool:
        if not self.is_configured():
            return False
        try:
            self.auth.get_access_token()
            return True
        except AuthError:
            return False

    def list_models(self) -> List[str]:
        # Intentionally empty: model selection is a server-side implementation
        # detail in Pixel CommandAI, not a user-facing choice.
        return []
