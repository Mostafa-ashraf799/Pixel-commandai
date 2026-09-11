"""
Auto Documentation Generator
------------------------------
يقرأ ملفات كود مشروع (أو ملف واحد) ويولّد توثيق Markdown احترافي تلقائيًا:
وصف عام، شرح الدوال/الكلاسات الرئيسية، وأمثلة استخدام لو ممكن استنتاجها.

يعتمد على الـ AI في التوليد، لكن بيبني الملخص المصدري بنفسه (بدون AI)
لتقليل استهلاك التوكنز وتفادي إرسال كود حساس بالكامل عند الحاجة.
"""

from pathlib import Path
from typing import List, Optional

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage


CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rb", ".php"}
IGNORED_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}


class DocGenerator:
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager

    def _collect_source_files(self, root: str, max_files: int = 30) -> List[Path]:
        root_path = Path(root)
        files = []
        for f in root_path.rglob("*"):
            if len(files) >= max_files:
                break
            if any(part in IGNORED_DIRS for part in f.parts):
                continue
            if f.is_file() and f.suffix in CODE_EXTENSIONS:
                files.append(f)
        return files

    def _build_code_digest(self, files: List[Path], max_chars_per_file: int = 1500) -> str:
        """يبني ملخص مضغوط من الملفات بدل إرسال الكود كامل (يوفر توكنز كتير)."""
        digest_parts = []
        for f in files:
            try:
                content = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            truncated = content[:max_chars_per_file]
            digest_parts.append(f"### الملف: {f}\n```\n{truncated}\n```")
        return "\n\n".join(digest_parts)

    def generate_project_docs(self, root: str = ".", max_files: int = 30) -> str:
        files = self._collect_source_files(root, max_files=max_files)
        if not files:
            return "لم يتم العثور على ملفات كود مدعومة في هذا المسار."

        digest = self._build_code_digest(files)

        messages = [
            ChatMessage(
                role="system",
                content=(
                    "أنت كاتب توثيق تقني محترف. بناءً على ملخص ملفات الكود التالية، "
                    "اكتب ملف README.md احترافي بصيغة Markdown يتضمن: "
                    "وصف عام للمشروع، طريقة التثبيت المتوقعة، شرح المكونات الرئيسية، "
                    "وأمثلة استخدام إن أمكن استنتاجها. لا تخترع معلومات غير موجودة في الكود."
                ),
            ),
            ChatMessage(role="user", content=digest),
        ]

        response = self.provider_manager.chat(messages, temperature=0.3, max_tokens=3000)
        return response.content if response.ok else f"❌ خطأ: {response.error}"

    def generate_file_docs(self, file_path: str) -> str:
        path = Path(file_path)
        if not path.exists():
            return f"الملف غير موجود: {file_path}"

        content = path.read_text(encoding="utf-8", errors="ignore")

        messages = [
            ChatMessage(
                role="system",
                content=(
                    "أنت كاتب توثيق تقني محترف. وثّق الكود التالي بصيغة Markdown: "
                    "وصف عام، شرح كل دالة/كلاس رئيسي بمدخلاته ومخرجاته، ومثال استخدام واحد بسيط."
                ),
            ),
            ChatMessage(role="user", content=content[:8000]),
        ]

        response = self.provider_manager.chat(messages, temperature=0.3, max_tokens=2000)
        return response.content if response.ok else f"❌ خطأ: {response.error}"

    def save_docs(self, content: str, output_path: str = "README_generated.md") -> str:
        path = Path(output_path)
        path.write_text(content, encoding="utf-8")
        return f"تم حفظ التوثيق في: {output_path}"
