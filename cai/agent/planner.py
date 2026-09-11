"""
Planner
-------
يحوّل طلب المستخدم بلغة طبيعية (مثال: "do Build Flask API") إلى خطة
منظمة من خطوات قابلة للتنفيذ، باستخدام الـ AI Provider الحالي.

الخطة بترجع كـ JSON منظم عشان باقي النظام (Agent Executor) يقدر
ينفذها خطوة خطوة.
"""

import json
import re
from dataclasses import dataclass, field
from typing import List, Optional

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage


PLANNER_SYSTEM_PROMPT = """أنت مخطِّط مهام داخل أداة CommandAI (cai) تعمل في Terminal.
مهمتك: تحويل طلب المستخدم إلى خطة تنفيذ منظمة كخطوات صغيرة وواضحة.

أعد الرد بصيغة JSON فقط بدون أي شرح إضافي وبدون Markdown، بالشكل التالي:
{
  "title": "عنوان مختصر للمهمة",
  "steps": [
    {"id": 1, "description": "وصف الخطوة", "command": "الأمر الفعلي إن وجد أو null"}
  ]
}

قواعد:
- إذا كانت الخطوة مجرد إجراء AI (مثل: توليد كود) اجعل command = null.
- إذا كانت الخطوة تحتاج أمر Terminal فعلي، اكتبه بدقة في command.
- اجعل الخطوات قصيرة وعملية (5 إلى 10 خطوات كحد أقصى عادة).
"""


@dataclass
class PlanStep:
    id: int
    description: str
    command: Optional[str] = None
    done: bool = False
    result: Optional[str] = None


@dataclass
class Plan:
    title: str
    steps: List[PlanStep] = field(default_factory=list)

    def pretty_print(self) -> str:
        lines = [f"Plan: {self.title}", ""]
        for step in self.steps:
            marker = "✔" if step.done else " "
            cmd_part = f"  →  {step.command}" if step.command else ""
            lines.append(f"[{marker}] {step.id}. {step.description}{cmd_part}")
        return "\n".join(lines)


class Planner:
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager

    def _extract_json(self, text: str) -> dict:
        # يتعامل مع حالة إن الموديل رجّع JSON ملفوف بـ ```json ... ```
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ValueError("لم يتم العثور على JSON صالح في رد النموذج.")
        return json.loads(match.group(0))

    def create_plan(self, user_request: str, context: str = "") -> Plan:
        messages = [
            ChatMessage(role="system", content=PLANNER_SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=f"سياق النظام:\n{context}\n\nطلب المستخدم:\n{user_request}",
            ),
        ]

        response = self.provider_manager.chat(messages, temperature=0.2, max_tokens=1500)

        if not response.ok:
            return Plan(title="فشل إنشاء الخطة", steps=[
                PlanStep(id=1, description=f"خطأ: {response.error}")
            ])

        try:
            data = self._extract_json(response.content)
            steps = [
                PlanStep(
                    id=s.get("id", i + 1),
                    description=s.get("description", ""),
                    command=s.get("command"),
                )
                for i, s in enumerate(data.get("steps", []))
            ]
            return Plan(title=data.get("title", user_request), steps=steps)
        except Exception:
            # فallback: خطة بخطوة واحدة تحتوي الرد الخام
            return Plan(
                title=user_request,
                steps=[PlanStep(id=1, description=response.content)],
            )
