"""
Gemini Provider
---------------
Adapter لـ Google Gemini API (generativelanguage.googleapis.com).
"""

import json
from typing import Any, Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from cai.providers.base_provider import BaseProvider, ChatMessage, ProviderResponse


class GeminiProvider(BaseProvider):
    name = "gemini"
    default_model = "gemini-2.5-pro"
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"

    def _to_gemini_contents(self, messages: List[ChatMessage]) -> Dict[str, Any]:
        system_parts = []
        contents = []
        for m in messages:
            if m.role == "system":
                system_parts.append(m.content)
            else:
                role = "model" if m.role == "assistant" else "user"
                contents.append({"role": role, "parts": [{"text": m.content}]})
        payload: Dict[str, Any] = {"contents": contents}
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
        return payload

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
            return ProviderResponse(content="", error="لا يوجد API key لـ Gemini.")

        model_name = model or self.default_model
        url = f"{self.BASE_URL}/models/{model_name}:generateContent?key={self.api_key}"

        payload = self._to_gemini_contents(messages)
        payload["generationConfig"] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }

        try:
            resp = requests.post(url, data=json.dumps(payload),
                                  headers={"Content-Type": "application/json"}, timeout=60)
            data = resp.json()

            if resp.status_code != 200:
                err_msg = data.get("error", {}).get("message", str(data))
                return ProviderResponse(content="", error=err_msg, raw=data)

            candidate = data["candidates"][0]
            parts = candidate.get("content", {}).get("parts", [])
            content = "".join(p.get("text", "") for p in parts)
            usage = data.get("usageMetadata", {})

            return ProviderResponse(
                content=content,
                raw=data,
                model=model_name,
                finish_reason=candidate.get("finishReason"),
                usage={
                    "prompt_tokens": usage.get("promptTokenCount", 0),
                    "completion_tokens": usage.get("candidatesTokenCount", 0),
                    "total_tokens": usage.get("totalTokenCount", 0),
                },
            )
        except Exception as e:
            return ProviderResponse(content="", error=str(e))

    def test_connection(self) -> bool:
        result = self.chat([ChatMessage(role="user", content="ping")], max_tokens=5)
        return result.ok

    def list_models(self) -> List[str]:
        if requests is None or not self.api_key:
            return []
        try:
            url = f"{self.BASE_URL}/models?key={self.api_key}"
            resp = requests.get(url, timeout=20)
            data = resp.json()
            return [m["name"].split("/")[-1] for m in data.get("models", [])]
        except Exception:
            return []
