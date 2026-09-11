"""
Agent Executor
--------------
يأخذ Plan جاهزة وينفذها خطوة خطوة:
- لو الخطوة عندها command: ينفذها عبر ExecutionEngine.
- لو فشلت: يحاول يحلل السبب عبر الـ AI ويقترح إصلاح (retry / fix / skip / stop).
- لو الخطوة AI-only (زي توليد كود): يبعتها للـ Provider مباشرة.
"""

from typing import Callable, Optional

from cai.agent.planner import Plan, PlanStep
from cai.engine.execution_engine import ExecutionEngine
from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage


FIX_SYSTEM_PROMPT = """أنت مساعد إصلاح أخطاء داخل أداة CommandAI (cai).
سيتم إعطاؤك أمر فشل مع رسالة الخطأ. اقترح أمرًا بديلاً واحدًا فقط لإصلاح المشكلة
أو أعد المتابعة. أعد الرد بأمر Terminal واحد فقط بدون أي شرح، أو أعد كلمة SKIP
إذا كان من الأفضل تجاوز الخطوة."""


class AgentExecutor:
    def __init__(
        self,
        execution_engine: ExecutionEngine,
        provider_manager: ProviderManager,
        on_step_start: Optional[Callable[[PlanStep], None]] = None,
        on_step_done: Optional[Callable[[PlanStep], None]] = None,
        max_retries: int = 2,
    ):
        self.engine = execution_engine
        self.provider_manager = provider_manager
        self.on_step_start = on_step_start
        self.on_step_done = on_step_done
        self.max_retries = max_retries

    def _attempt_fix(self, step: PlanStep, error_output: str) -> Optional[str]:
        messages = [
            ChatMessage(role="system", content=FIX_SYSTEM_PROMPT),
            ChatMessage(
                role="user",
                content=f"الأمر الذي فشل:\n{step.command}\n\nرسالة الخطأ:\n{error_output}",
            ),
        ]
        response = self.provider_manager.chat(messages, temperature=0.2, max_tokens=300)
        if not response.ok:
            return None
        suggestion = response.content.strip().strip("`")
        if suggestion.upper() == "SKIP":
            return None
        return suggestion

    def run_plan(self, plan: Plan) -> Plan:
        for step in plan.steps:
            if self.on_step_start:
                self.on_step_start(step)

            if step.command:
                attempts = 0
                result = self.engine.run(step.command)

                while not result.success and not result.was_blocked and attempts < self.max_retries:
                    attempts += 1
                    fix_command = self._attempt_fix(step, result.stderr or result.stdout)
                    if not fix_command:
                        break
                    step.command = fix_command
                    result = self.engine.run(step.command)

                step.done = result.success
                step.result = self.engine.analyze_result(result)
            else:
                # خطوة AI فقط بدون أمر تنفيذي
                step.done = True
                step.result = "تمت معالجتها بواسطة الذكاء الاصطناعي مباشرة."

            if self.on_step_done:
                self.on_step_done(step)

            if not step.done:
                break  # نوقف عند أول خطوة فاشلة بدون حل

        return plan
