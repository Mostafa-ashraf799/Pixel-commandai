"""
Context Manager
-----------------
نسخة موسّعة من AutoContextEngine (v2) بتجمع صورة شاملة لحالة النظام
والمحادثة قبل أي طلب AI: المحادثة الأخيرة، المجلد الحالي، حالة Git،
نظام التشغيل، إصدار Python، الملفات المفتوحة مؤخرًا، آخر الأوامر،
وآخر الأخطاء.

الفرق عن AutoContextEngine: ده بيجمع من مصادر متعددة (Memory, History,
ExecutionEngine, Git) في كائن واحد منظم (ContextSnapshot) بدل ملخص نصي
بسيط، وبيسمح بالتحكم في أي أجزاء تتضمن حسب نوع الطلب (توفير توكنز).
"""

import os
import platform
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from cai.engine.execution_engine import ExecutionEngine
from cai.memory.memory_manager import MemoryManager
from cai.memory.history_manager import HistoryManager


@dataclass
class ContextSnapshot:
    os_name: str = ""
    python_version: str = ""
    current_folder: str = ""
    git_branch: Optional[str] = None
    git_uncommitted: Optional[int] = None
    open_files: List[str] = field(default_factory=list)
    last_commands: List[str] = field(default_factory=list)
    last_errors: List[str] = field(default_factory=list)
    recent_conversation: List[str] = field(default_factory=list)

    def to_prompt_text(self) -> str:
        lines = [
            f"OS: {self.os_name} | Python: {self.python_version}",
            f"المجلد الحالي: {self.current_folder}",
        ]
        if self.git_branch:
            lines.append(f"Git branch: {self.git_branch} | تغييرات غير محفوظة: {self.git_uncommitted}")
        if self.open_files:
            lines.append(f"ملفات مفتوحة مؤخرًا: {', '.join(self.open_files)}")
        if self.last_commands:
            lines.append(f"آخر الأوامر: {' | '.join(self.last_commands)}")
        if self.last_errors:
            lines.append(f"آخر الأخطاء: {' | '.join(self.last_errors)}")
        if self.recent_conversation:
            lines.append("آخر المحادثة:\n" + "\n".join(self.recent_conversation))
        return "\n".join(lines)


class ContextManager:
    def __init__(self, engine: ExecutionEngine, memory: MemoryManager, history: HistoryManager):
        self.engine = engine
        self.memory = memory
        self.history = history
        self._open_files: List[str] = []  # يُحدَّث من CommandRouter عند كل edit/read

    def track_open_file(self, path: str, max_tracked: int = 10) -> None:
        if path in self._open_files:
            self._open_files.remove(path)
        self._open_files.insert(0, path)
        self._open_files = self._open_files[:max_tracked]

    def _git_info(self, root: str = "."):
        branch_result = self.engine.run("git rev-parse --abbrev-ref HEAD", cwd=root)
        branch = branch_result.stdout.strip() if branch_result.success else None

        uncommitted = None
        if branch:
            status_result = self.engine.run("git status --porcelain", cwd=root)
            if status_result.success:
                uncommitted = len([l for l in status_result.stdout.splitlines() if l.strip()])

        return branch, uncommitted

    def build_snapshot(
        self,
        include_conversation: bool = True,
        include_git: bool = True,
        conversation_limit: int = 6,
    ) -> ContextSnapshot:
        snapshot = ContextSnapshot(
            os_name=platform.system(),
            python_version=".".join(map(str, sys.version_info[:3])),
            current_folder=os.getcwd(),
            open_files=list(self._open_files),
            last_commands=self.history.last(5),
        )

        if include_git:
            branch, uncommitted = self._git_info()
            snapshot.git_branch = branch
            snapshot.git_uncommitted = uncommitted

        # آخر الأخطاء من ملف memory (errors.jsonl)
        errors_path = self.memory.errors_path
        if errors_path.exists():
            try:
                import json
                with open(errors_path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-3:]
                snapshot.last_errors = [
                    json.loads(l).get("error", "")[:100] for l in lines if l.strip()
                ]
            except (json.JSONDecodeError, OSError):
                pass

        if include_conversation:
            recent = self.memory.recent_messages(conversation_limit)
            snapshot.recent_conversation = [f"[{m['role']}] {m['content'][:150]}" for m in recent]

        return snapshot

    def build_prompt_context(self, **kwargs) -> str:
        return self.build_snapshot(**kwargs).to_prompt_text()
