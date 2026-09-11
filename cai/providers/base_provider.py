"""
Base Provider
-------------
الواجهة الموحدة (Interface) اللي كل Provider (OpenAI, Gemini, Groq,
OpenRouter, Ollama...) لازم يطبّقها.

الهدف: باقي أجزاء البرنامج (Agent, Execution Engine, Commands)
تتعامل مع أي Provider بنفس الطريقة تمامًا، من غير ما تعرف تفاصيله.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Iterator, List, Optional


@dataclass
class ChatMessage:
    role: str          # "system" | "user" | "assistant" | "tool"
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None


@dataclass
class ProviderResponse:
    content: str
    raw: Any = None
    model: Optional[str] = None
    finish_reason: Optional[str] = None
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    usage: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None

    @property
    def ok(self) -> bool:
        return self.error is None


class BaseProvider(ABC):
    """كل Provider جديد يورث من الكلاس ده ويطبّق الدوال دي."""

    name: str = "base"
    default_model: str = ""

    def __init__(self, api_key: Optional[str] = None, **kwargs):
        self.api_key = api_key
        self.extra_config = kwargs

    @abstractmethod
    def chat(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 2000,
        tools: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> ProviderResponse:
        """يرسل محادثة كاملة ويرجع رد واحد (non-streaming)."""
        raise NotImplementedError

    def chat_stream(
        self,
        messages: List[ChatMessage],
        model: Optional[str] = None,
        temperature: float = 0.4,
        max_tokens: int = 2000,
        **kwargs,
    ) -> Iterator[str]:
        """
        Streaming افتراضي: لو الـ Provider ما بيدعمش streaming حقيقي،
        نرجع الرد كامل كقطعة واحدة كحل بديل.
        """
        response = self.chat(messages, model=model, temperature=temperature,
                              max_tokens=max_tokens, **kwargs)
        yield response.content

    @abstractmethod
    def test_connection(self) -> bool:
        """اختبار سريع إن المفتاح شغال والاتصال تمام."""
        raise NotImplementedError

    @abstractmethod
    def list_models(self) -> List[str]:
        """يرجع قائمة الموديلات المتاحة لهذا الـ Provider."""
        raise NotImplementedError

    def is_configured(self) -> bool:
        return bool(self.api_key) or self.name == "ollama"
