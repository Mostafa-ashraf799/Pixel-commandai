"""
Script Generator
------------------
يولّد سكريبتات كاملة وجاهزة للتشغيل (bash, python, PowerShell) بناءً على
وصف طبيعي، ويحفظها مباشرة كملف قابل للتنفيذ (مع صلاحيات تنفيذ في Linux/macOS).
"""

import os
import platform
import stat
from pathlib import Path
from typing import Optional

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage


LANGUAGE_HINTS = {
    "bash": {"ext": ".sh", "shebang": "#!/bin/bash\n"},
    "python": {"ext": ".py", "shebang": "#!/usr/bin/env python3\n"},
    "powershell": {"ext": ".ps1", "shebang": ""},
}

SYSTEM_PROMPT = """أنت مولّد سكريبتات محترف. اكتب سكريبت {language} كامل وجاهز للتنفيذ
مباشرة بناءً على الوصف التالي. أضف تعليقات مختصرة للخطوات المهمة فقط.
أعد الكود فقط بدون أي شرح خارجي وبدون Markdown code fences."""


class ScriptGenerator:
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager
        self.os_name = platform.system()

    def default_language(self) -> str:
        return "powershell" if self.os_name == "Windows" else "bash"

    def _clean_output(self, text: str) -> str:
        cleaned = text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        return cleaned.strip()

    def generate(self, description: str, language: Optional[str] = None) -> str:
        language = (language or self.default_language()).lower()
        system_prompt = SYSTEM_PROMPT.format(language=language)
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=description),
        ]
        response = self.provider_manager.chat(messages, temperature=0.25, max_tokens=2000)
        if not response.ok:
            return f"❌ خطأ: {response.error}"
        return self._clean_output(response.content)

    def generate_and_save(
        self, description: str, output_path: str, language: Optional[str] = None
    ) -> str:
        language = (language or self.default_language()).lower()
        hint = LANGUAGE_HINTS.get(language, LANGUAGE_HINTS["bash"])

        code = self.generate(description, language=language)
        if code.startswith("❌"):
            return code

        path = Path(output_path)
        if path.suffix == "":
            path = path.with_suffix(hint["ext"])

        content = code
        if hint["shebang"] and not code.startswith("#!"):
            content = hint["shebang"] + code

        path.write_text(content, encoding="utf-8")

        if self.os_name != "Windows" and language in ("bash", "python"):
            current = path.stat().st_mode
            path.chmod(current | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

        return f"تم إنشاء السكريبت: {path}\nنوع اللغة: {language}"
