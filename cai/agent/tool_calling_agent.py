"""
Tool-Calling Agent
---------------------
هنا بيحصل الفرق الحقيقي عن v1/v2: بدل Planner بيولّد خطة نصية ثابتة
والـ Executor بينفذها كأوامر shell، الـ Agent ده بيدير محادثة حقيقية
مع الـ AI فيها Tool Calling:

1. يبعت للـ AI: رسالة المستخدم + قائمة الأدوات المتاحة (JSON Schema).
2. الـ AI يرد إما بنص عادي (خلص) أو بـ tool_calls (عايز ينفذ أداة).
3. لو فيه tool_calls: الـ Agent ينفذهم فعليًا عبر ToolRegistry.call()،
   ويرجع النتيجة للـ AI كرسالة "tool" جديدة في نفس المحادثة.
4. يتكرر لحد ما الـ AI يرد بنص نهائي بدون طلب أدوات جديدة (أو نوصل
   لحد أقصى من الجولات لتفادي loop لا نهائي).

ده أقرب فعليًا لـ Function Calling الحقيقي المستخدم في OpenAI/Claude/Gemini،
بدل محاكاة عبر توليد نص Shell وتفسيره لاحقًا.
"""

import json
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage
from cai.tools_registry.tool_registry import ToolRegistry


SYSTEM_PROMPT = """أنت CommandAI (cai)، وكيل ذكاء اصطناعي يعمل داخل Terminal.
لديك أدوات حقيقية يمكنك استدعاؤها مباشرة (قراءة/كتابة ملفات، Git، تنفيذ أوامر،
فحص الشبكة، حالة النظام). استخدم الأداة الأنسب دائمًا بدل افتراض النتيجة.
لا تطلب من المستخدم تنفيذ الأمر بنفسه — نفّذه أنت عبر الأداة المناسبة.
بعد تنفيذ الأدوات اللازمة، لخّص النتيجة للمستخدم بوضوح ودون تكرار تفاصيل تقنية زائدة."""


@dataclass
class ToolCallTrace:
    tool_name: str
    arguments: dict
    success: bool
    result_preview: str


@dataclass
class AgentRunResult:
    final_response: str
    trace: List[ToolCallTrace] = field(default_factory=list)
    rounds_used: int = 0


class ToolCallingAgent:
    def __init__(self, provider_manager: ProviderManager, tool_registry: ToolRegistry):
        self.provider_manager = provider_manager
        self.tools = tool_registry

    def run(
        self,
        user_message: str,
        context: str = "",
        max_rounds: int = 6,
        confirm_callback: Optional[Callable] = None,
        on_tool_call: Optional[Callable[[ToolCallTrace], None]] = None,
    ) -> AgentRunResult:
        system_content = SYSTEM_PROMPT
        if context:
            system_content += f"\n\nسياق بيئة العمل الحالية:\n{context}"

        messages = [
            ChatMessage(role="system", content=system_content),
            ChatMessage(role="user", content=user_message),
        ]

        schemas = self.tools.get_schemas()
        trace: List[ToolCallTrace] = []

        for round_num in range(1, max_rounds + 1):
            response = self.provider_manager.chat(messages, tools=schemas, temperature=0.3, max_tokens=2000)

            if not response.ok:
                return AgentRunResult(final_response=f"❌ خطأ: {response.error}", trace=trace, rounds_used=round_num)

            if not response.tool_calls:
                # الـ AI رد بنص نهائي، مفيش أدوات مطلوبة -> انتهت المهمة
                return AgentRunResult(final_response=response.content, trace=trace, rounds_used=round_num)

            # الـ AI عايز ينفذ أداة/أدوات -> ننفذها فعليًا ونرجع النتيجة له
            messages.append(ChatMessage(role="assistant", content=response.content or ""))

            for call in response.tool_calls:
                function_info = call.get("function", {})
                tool_name = function_info.get("name", "")
                try:
                    arguments = json.loads(function_info.get("arguments", "{}"))
                except json.JSONDecodeError:
                    arguments = {}

                result = self.tools.call(tool_name, arguments, confirm_callback=confirm_callback)

                trace_entry = ToolCallTrace(
                    tool_name=tool_name,
                    arguments=arguments,
                    success=result.success,
                    result_preview=str(result.result or result.error)[:200],
                )
                trace.append(trace_entry)
                if on_tool_call:
                    on_tool_call(trace_entry)

                messages.append(ChatMessage(
                    role="tool",
                    content=result.to_message_content(),
                    tool_call_id=call.get("id"),
                    name=tool_name,
                ))

        return AgentRunResult(
            final_response="⚠️ تم الوصول للحد الأقصى من جولات استدعاء الأدوات بدون نتيجة نهائية.",
            trace=trace,
            rounds_used=max_rounds,
        )
