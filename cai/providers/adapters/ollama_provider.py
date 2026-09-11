"""
Ollama Provider
---------------
Adapter للنماذج المحلية اللي تشتغل عن طريق Ollama (http://localhost:11434).
لا يحتاج API key.
"""

import json
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from cai.providers.base_provider import BaseProvider, ChatMessage, ProviderResponse


class OllamaProvider(BaseProvider):
    name = "ollama"
    default_model = "llama3.2"

    def __init__(self, api_key: Optional[str] = None, base_url: str = "http://localhost:11434", **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        self.base_url = base_url

    def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ProviderResponse:
        if requests is None:
            return ProviderResponse(content="", error="مكتبة requests غير مثبتة.")

        payload = {
            "model": model or self.default_model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "stream": False,
            "options": {"temperature": temperature, "num_predict": max_tokens},
        }

        try:
            resp = requests.post(f"{self.base_url}/api/chat", data=json.dumps(payload), timeout=120)
            data = resp.json()

            if resp.status_code != 200:
                return ProviderResponse(content="", error=data.get("error", str(data)))

            content = data.get("message", {}).get("content", "")
            return ProviderResponse(content=content, raw=data, model=payload["model"])
        except Exception as e:
            return ProviderResponse(
                content="",
                error=f"تعذر الاتصال بـ Ollama محليًا ({e}). تأكد إن Ollama شغال.",
            )

    def test_connection(self) -> bool:
        if requests is None:
            return False
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False

    def list_models(self) -> List[str]:
        if requests is None:
            return []
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=10)
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def is_configured(self) -> bool:
        return True  # لا يحتاج API key
