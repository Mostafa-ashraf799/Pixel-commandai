"""
Code Assistant
--------------
يوفر عمليات البرمجة الأساسية عبر الـ AI Provider: كتابة كود، تعديل،
شرح، Debug، Review، Refactor. النتائج نصية ترجع للـ Command Router
اللي بيقرر يطبعها أو يكتبها في ملف.
"""

from pathlib import Path
from typing import Optional

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage


class CodeAssistant:
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager

    def _ask(self, system_prompt: str, user_content: str, max_tokens: int = 2000) -> str:
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_content),
        ]
        response = self.provider_manager.chat(messages, temperature=0.3, max_tokens=max_tokens)
        return response.content if response.ok else f"❌ خطأ: {response.error}"

    def write_code(self, description: str, language: str = "") -> str:
        system = (
            "أنت مبرمج خبير. اكتب كودًا نظيفًا وعمليًا فقط بناءً على الطلب. "
            "لا تشرح إلا إذا طُلب منك ذلك صراحة. ضع الكود داخل code block واضح."
        )
        lang_hint = f" بلغة {language}" if language else ""
        return self._ask(system, f"اكتب كود{lang_hint} لتنفيذ:\n{description}")

    def explain_code(self, code: str) -> str:
        system = "أنت مبرمج خبير. اشرح الكود التالي بشكل مبسط وواضح خطوة بخطوة."
        return self._ask(system, code)

    def debug_code(self, code: str, error_message: str = "") -> str:
        system = (
            "أنت خبير Debug. حلل الكود التالي ورسالة الخطأ إن وجدت، "
            "وحدد سبب المشكلة بدقة، واقترح الإصلاح كاملاً."
        )
        content = f"الكود:\n{code}"
        if error_message:
            content += f"\n\nرسالة الخطأ:\n{error_message}"
        return self._ask(system, content)

    def review_code(self, code: str) -> str:
        system = (
            "أنت مراجع كود محترف (Code Reviewer). راجع الكود التالي من ناحية: "
            "الأداء، الأمان، القراءة، أفضل الممارسات. اذكر الملاحظات كنقاط مرتبة."
        )
        return self._ask(system, code)

    def refactor_code(self, code: str, goal: str = "تحسين القراءة والأداء") -> str:
        system = f"أنت مبرمج خبير. أعد هيكلة (Refactor) الكود التالي بهدف: {goal}. أعد الكود الكامل بعد التحسين."
        return self._ask(system, code)

    def edit_file(self, file_path: str, instruction: str) -> str:
        """يقرأ ملف، يعدله حسب التعليمات، ويكتب النسخة الجديدة."""
        path = Path(file_path)
        if not path.exists():
            return f"الملف غير موجود: {file_path}"

        original = path.read_text(encoding="utf-8", errors="ignore")
        system = (
            "أنت مبرمج خبير. لديك ملف كود كامل وتعليمات تعديل. "
            "أعد محتوى الملف كاملاً بعد تطبيق التعديل المطلوب فقط، بدون أي شرح إضافي."
        )
        content = f"محتوى الملف الحالي:\n{original}\n\nالتعديل المطلوب:\n{instruction}"
        new_content = self._ask(system, content, max_tokens=4000)

        # تنظيف بسيط لو الرد اتلف بـ code fences
        cleaned = new_content.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])

        path.write_text(cleaned, encoding="utf-8")
        return f"تم تعديل الملف: {file_path}"
