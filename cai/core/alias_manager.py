"""
Smart Alias System
--------------------
يسمح للمستخدم بتعريف اختصارات خاصة به لأوامر أو تسلسل أوامر بيستخدمها
كتير، زي alias في bash لكن مدمج داخل cai نفسه وبيدعم استبدال متغيرات.

مثال:
    alias add deploy = git push && docker compose up -d --build
    alias add morning = dash; git status

بعدين كتابة "deploy" أو "morning" هتُنفّذ التسلسل المحفوظ بالكامل.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional


class AliasManager:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.aliases_path = self.base_dir / "aliases.json"
        self._aliases: Dict[str, str] = self._load()

    def _load(self) -> Dict[str, str]:
        if not self.aliases_path.exists():
            return {}
        try:
            with open(self.aliases_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self) -> None:
        with open(self.aliases_path, "w", encoding="utf-8") as f:
            json.dump(self._aliases, f, indent=2, ensure_ascii=False)

    def add(self, name: str, expansion: str) -> str:
        name = name.strip().lower()
        if not name or not expansion:
            return "استخدم: alias add <اسم> = <أمر أو تسلسل أوامر>"
        self._aliases[name] = expansion.strip()
        self._save()
        return f"تم حفظ الاختصار: {name} → {expansion.strip()}"

    def remove(self, name: str) -> str:
        name = name.strip().lower()
        if name in self._aliases:
            del self._aliases[name]
            self._save()
            return f"تم حذف الاختصار: {name}"
        return f"الاختصار غير موجود: {name}"

    def get(self, name: str) -> Optional[str]:
        return self._aliases.get(name.strip().lower())

    def list_all(self) -> Dict[str, str]:
        return dict(self._aliases)

    def expand(self, user_input: str) -> Optional[List[str]]:
        """
        لو أول كلمة في المدخل هي alias معروف، يرجع قائمة الأوامر الناتجة
        بعد فك التسلسل (مفصولة بـ ; أو &&)، وإلا يرجع None.
        """
        first_word = user_input.strip().split(" ", 1)[0].lower()
        expansion = self._aliases.get(first_word)
        if not expansion:
            return None

        # يدعم فصل بسيط بين أوامر متعددة داخل نفس الـ alias
        separators = ["&&", ";"]
        commands = [expansion]
        for sep in separators:
            new_commands = []
            for cmd in commands:
                new_commands.extend([c.strip() for c in cmd.split(sep)])
            commands = new_commands

        return [c for c in commands if c]

    def render_list(self) -> str:
        if not self._aliases:
            return "لا توجد اختصارات محفوظة بعد. استخدم: alias add <اسم> = <أمر>"
        lines = ["الاختصارات المحفوظة:"]
        for name, expansion in self._aliases.items():
            lines.append(f"  {name:<15} → {expansion}")
        return "\n".join(lines)
