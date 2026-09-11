"""
OpenAI-Compatible Provider
---------------------------
Provider واحد عام يشتغل مع أي API متوافق مع OpenAI Chat Completions format.
ده بيغطي: OpenAI, Groq, OpenRouter, DeepSeek, وأي provider تاني بنفس الـ schema.

الفرق بينهم بس في:
- base_url
- بعض الـ headers الإضافية (زي OpenRouter اللي محتاج Referer/Title)
"""

import json
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from cai.providers.base_provider import BaseProvider, ChatMessage, ProviderResponse


class OpenAICompatibleProvider(BaseProvider):
    """
    provider_name: اسم قصير للعرض (openai / groq / openrouter / deepseek)
    base_url: رابط الـ API الأساسي (بدون /chat/completions)
    """

    PRESETS = {
        "openai": {
            "base_url": "https://api.openai.com/v1",
            "default_model": "gpt-4o-mini",
        },
        "groq": {
            "base_url": "https://api.groq.com/openai/v1",
            "default_model": "llama-3.3-70b-versatile",
        },
        "openrouter": {
            "base_url": "https://openrouter.ai/api/v1",
            "default_model": "openrouter/auto",
        },
        "deepseek": {
            "base_url": "https://api.deepseek.com/v1",
            "default_model": "deepseek-chat",
        },
    }

    def __init__(self, provider_name: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(api_key=api_key, **kwargs)
        preset = self.PRESETS.get(provider_name, {})
        self.name = provider_name
        self.base_url = kwargs.get("base_url", preset.get("base_url"))
        self.default_model = kwargs.get("default_model", preset.get("default_model", ""))

    def _headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
        }
        if self.name == "openrouter":
            headers["HTTP-Referer"] = "https://cai.local"
            headers["X-Title"] = "CommandAI (cai)"
        return headers

    def _to_api_message(self, m: ChatMessage) -> Dict[str, Any]:
        msg: Dict[str, Any] = {"role": m.role, "content": m.content}
        if m.role == "tool":
            if m.tool_call_id:
                msg["tool_call_id"] = m.tool_call_id
            if m.name:
                msg["name"] = m.name
        return msg

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

        if not self.api_key:
            return ProviderResponse(content="", error=f"لا يوجد API key لـ {self.name}.")

        payload: Dict[str, Any] = {
            "model": model or self.default_model,
            "messages": [self._to_api_message(m) for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if tools:
            payload["tools"] = tools

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=self._headers(),
                data=json.dumps(payload),
                timeout=60,
            )
            data = resp.json()

            if resp.status_code != 200:
                err_msg = data.get("error", {}).get("message", str(data))
                return ProviderResponse(content="", error=err_msg, raw=data)

            choice = data["choices"][0]
            content = choice["message"].get("content") or ""
            tool_calls = choice["message"].get("tool_calls", []) or []
            usage = data.get("usage", {})

            return ProviderResponse(
                content=content,
                raw=data,
                model=data.get("model"),
                finish_reason=choice.get("finish_reason"),
                tool_calls=tool_calls,
                usage=usage,
            )
        except Exception as e:
            return ProviderResponse(content="", error=str(e))

    def test_connection(self) -> bool:
        result = self.chat(
            [ChatMessage(role="user", content="ping")],
            max_tokens=5,
        )
        return result.ok

    def list_models(self) -> List[str]:
        if requests is None or not self.api_key:
            return []
        try:
            resp = requests.get(f"{self.base_url}/models", headers=self._headers(), timeout=20)
            data = resp.json()
            return [m["id"] for m in data.get("data", [])]
        except Exception:
            return []
