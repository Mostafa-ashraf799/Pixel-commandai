"""
AI Roles
--------
بدل Agent واحد بشخصية عامة، النظام ده بيعرّف أدوار متخصصة (Coder,
Reviewer, Debugger, Architect, Linux Expert, Windows Expert,
Security Expert, Git Expert) كل واحد له prompt مستقل (من prompts/)
ومعاملات توليد مناسبة له (temperature أقل للأمان، أعلى للإبداع...).

الـ RoleSelector في النهاية هو المسؤول عن اختيار الدور الأنسب تلقائيًا
بناءً على طلب المستخدم، عشان المستخدم مايحتاجش يحدد الدور يدويًا كل مرة
(لكن يقدر برضه لو عايز تحكم صريح، عبر أمر role).
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional

from cai.core.prompt_loader import PromptLoader
from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage


@dataclass
class AIRole:
    key: str
    display_name: str
    prompt_file: str
    temperature: float = 0.3
    keywords: List[str] = None  # كلمات مفتاحية تساعد RoleSelector على الاختيار التلقائي


ROLES: Dict[str, AIRole] = {
    "coder": AIRole("coder", "Coder", "coder", temperature=0.3,
                     keywords=["اكتب", "write", "implement", "function", "class", "كود"]),
    "reviewer": AIRole("reviewer", "Reviewer", "reviewer", temperature=0.2,
                        keywords=["راجع", "review", "check my code", "audit"]),
    "debugger": AIRole("debugger", "Debugger", "fixer", temperature=0.2,
                        keywords=["error", "خطأ", "crash", "traceback", "exception", "bug", "fix"]),
    "architect": AIRole("architect", "Architect", "architect", temperature=0.4,
                         keywords=["design", "architecture", "تصميم", "هيكلة", "structure"]),
    "linux_expert": AIRole("linux_expert", "Linux Expert", "linux", temperature=0.2,
                            keywords=["linux", "لينكس", "apt", "bash", "ubuntu", "kali"]),
    "windows_expert": AIRole("windows_expert", "Windows Expert", "windows", temperature=0.2,
                              keywords=["windows", "ويندوز", "powershell", "cmd", "winget"]),
    "security_expert": AIRole("security_expert", "Security Expert", "security", temperature=0.2,
                               keywords=["security", "أمان", "vulnerability", "ثغرة", "hack", "pentest"]),
    "git_expert": AIRole("git_expert", "Git Expert", "git", temperature=0.2,
                          keywords=["git", "commit", "branch", "merge", "rebase", "conflict"]),
}


class RoleSelector:
    def __init__(self, provider_manager: ProviderManager, prompt_loader: Optional[PromptLoader] = None):
        self.provider_manager = provider_manager
        self.prompts = prompt_loader or PromptLoader()

    def detect_role(self, user_message: str) -> AIRole:
        """اختيار تلقائي بسيط عبر كلمات مفتاحية؛ افتراضي = coder لو مفيش تطابق واضح."""
        lowered = user_message.lower()
        best_match: Optional[AIRole] = None
        best_score = 0

        for role in ROLES.values():
            score = sum(1 for kw in (role.keywords or []) if re.search(re.escape(kw.lower()), lowered))
            if score > best_score:
                best_score = score
                best_match = role

        return best_match or ROLES["coder"]

    def list_roles(self) -> List[str]:
        return list(ROLES.keys())

    def get_role(self, key: str) -> Optional[AIRole]:
        return ROLES.get(key)

    def ask_as(self, role_key: str, message: str, max_tokens: int = 1500) -> str:
        role = self.get_role(role_key)
        if not role:
            return f"دور غير معروف: {role_key}. الأدوار المتاحة: {', '.join(self.list_roles())}"

        system_prompt = self.prompts.load(role.prompt_file)
        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=message),
        ]
        response = self.provider_manager.chat(messages, temperature=role.temperature, max_tokens=max_tokens)
        return response.content if response.ok else f"❌ خطأ: {response.error}"

    def ask_auto(self, message: str, max_tokens: int = 1500) -> tuple:
        """يختار الدور تلقائيًا وينفذ الطلب، يرجع (اسم الدور المختار, الرد)."""
        role = self.detect_role(message)
        response = self.ask_as(role.key, message, max_tokens=max_tokens)
        return role.display_name, response
