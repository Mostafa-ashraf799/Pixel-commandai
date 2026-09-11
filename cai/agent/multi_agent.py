"""
Multi-Agent Collaboration
--------------------------
بدل ما يكون فيه Agent واحد بيعمل كل حاجة، النظام ده بيوزع مهمة معقدة
على فريق من الوكلاء المتخصصين، كل واحد له دور واضح:

- Architect  : يحلل الطلب ويحدد التصميم العام والخطوات الكبرى.
- Coder      : يكتب الكود الفعلي بناءً على تصميم الـ Architect.
- Reviewer   : يراجع كود الـ Coder ويكتشف المشاكل قبل التنفيذ.
- Executor   : ينفذ الأوامر الفعلية على النظام (عبر ExecutionEngine).
- Fixer      : يتدخل فقط لما حاجة تفشل، يحلل السبب ويقترح حل.

الفكرة: نفس فلسفة "فريق عمل حقيقي" بدل عامل واحد بيعمل كل حاجة،
مما يرفع جودة النتيجة النهائية للمهام المعقدة (زي "do build a saas app").
"""

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage
from cai.engine.execution_engine import ExecutionEngine
from cai.core.prompt_loader import PromptLoader


@dataclass
class AgentMessage:
    agent: str
    content: str


@dataclass
class CollaborationResult:
    task: str
    transcript: List[AgentMessage] = field(default_factory=list)
    final_code: Optional[str] = None
    execution_log: List[str] = field(default_factory=list)
    success: bool = True


class MultiAgentTeam:
    def __init__(self, provider_manager: ProviderManager, engine: Optional[ExecutionEngine] = None,
                 prompt_loader: Optional[PromptLoader] = None):
        self.provider_manager = provider_manager
        self.engine = engine
        self.prompts = prompt_loader or PromptLoader()

    def _ask(self, system_prompt: str, content: str, max_tokens: int = 2000) -> str:
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=content),
        ]
        response = self.provider_manager.chat(messages, temperature=0.3, max_tokens=max_tokens)
        return response.content if response.ok else f"[خطأ]: {response.error}"

    def run(
        self,
        task: str,
        max_review_cycles: int = 2,
        on_agent_update: Optional[Callable[[AgentMessage], None]] = None,
    ) -> CollaborationResult:
        result = CollaborationResult(task=task)

        def emit(agent: str, content: str):
            msg = AgentMessage(agent=agent, content=content)
            result.transcript.append(msg)
            if on_agent_update:
                on_agent_update(msg)

        # 1. Architect يحلل الطلب
        design = self._ask(self.prompts.load("architect"), task)
        emit("Architect", design)

        # 2. Coder يكتب الكود بناءً على التصميم
        coder_input = f"طلب المستخدم:\n{task}\n\nتصميم Architect:\n{design}"
        code = self._ask(self.prompts.load("coder"), coder_input, max_tokens=3000)
        emit("Coder", code)

        # 3. دورة مراجعة/إصلاح (Reviewer <-> Fixer) حتى الموافقة أو نفاذ المحاولات
        for cycle in range(max_review_cycles):
            review = self._ask(self.prompts.load("reviewer"), code, max_tokens=800)
            emit("Reviewer", review)

            if review.strip().upper().startswith("APPROVED"):
                break

            fixer_input = f"الكود الحالي:\n{code}\n\nملاحظات المراجعة:\n{review}"
            code = self._ask(self.prompts.load("fixer"), fixer_input, max_tokens=3000)
            emit("Fixer", code)

        result.final_code = code
        return result

    def run_with_execution(
        self,
        task: str,
        file_path: str,
        on_agent_update: Optional[Callable[[AgentMessage], None]] = None,
    ) -> CollaborationResult:
        """نفس run() لكن كمان يكتب الكود النهائي لملف وينفذه إن كان قابلاً للتنفيذ."""
        result = self.run(task, on_agent_update=on_agent_update)

        if self.engine and result.final_code:
            cleaned = result.final_code.strip()
            if cleaned.startswith("```"):
                lines = cleaned.split("\n")
                cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(cleaned)
            result.execution_log.append(f"تم حفظ الكود في: {file_path}")

        return result
