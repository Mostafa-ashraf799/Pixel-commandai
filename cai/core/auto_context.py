"""
Auto Context Engine
---------------------
ميزة خرافية: بدل ما تقول للـ AI "أنا شغال على مشروع Flask فيه كذا وكذا"،
النظام ده بيكتشف تلقائيًا من مجلد العمل الحالي:
- نوع المشروع (Python/Node/Rust/Docker/Git...).
- الملفات الرئيسية والمكتبات المستخدمة.
- حالة Git الحالية (فيه تغييرات غير محفوظة؟ على أي Branch؟).

وبعدين يحقن السياق ده تلقائيًا في أي محادثة أو خطة، عشان ردود الـ AI
تبقى مبنية على واقع مشروعك الفعلي مش تخمين عام.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional

from cai.engine.execution_engine import ExecutionEngine


PROJECT_MARKERS = {
    "Python": ["requirements.txt", "pyproject.toml", "setup.py", "Pipfile"],
    "Node.js": ["package.json"],
    "Rust": ["Cargo.toml"],
    "Go": ["go.mod"],
    "Docker": ["Dockerfile", "docker-compose.yml"],
    "PHP": ["composer.json"],
    "Ruby": ["Gemfile"],
}


class AutoContextEngine:
    def __init__(self, engine: Optional[ExecutionEngine] = None):
        self.engine = engine

    def detect_project_types(self, root: str = ".") -> List[str]:
        root_path = Path(root)
        detected = []
        for name, markers in PROJECT_MARKERS.items():
            if any((root_path / m).exists() for m in markers):
                detected.append(name)
        return detected

    def detect_key_files(self, root: str = ".", limit: int = 15) -> List[str]:
        root_path = Path(root)
        priority_names = [
            "README.md", "main.py", "app.py", "index.js", "package.json",
            "requirements.txt", "Dockerfile", "docker-compose.yml", ".env.example",
        ]
        found = [f for f in priority_names if (root_path / f).exists()]
        return found[:limit]

    def git_context(self, root: str = ".") -> Dict[str, str]:
        if not self.engine:
            return {}
        info = {}

        branch_result = self.engine.run("git rev-parse --abbrev-ref HEAD", cwd=root)
        if branch_result.success:
            info["branch"] = branch_result.stdout.strip()

        status_result = self.engine.run("git status --porcelain", cwd=root)
        if status_result.success:
            changes = [l for l in status_result.stdout.splitlines() if l.strip()]
            info["uncommitted_changes"] = str(len(changes))

        return info

    def build_context_summary(self, root: str = ".") -> str:
        """يبني ملخص نصي جاهز للحقن كسياق نظام قبل أي طلب AI."""
        root_path = Path(root).resolve()
        project_types = self.detect_project_types(root)
        key_files = self.detect_key_files(root)
        git_info = self.git_context(root)

        lines = [f"مجلد العمل الحالي: {root_path}"]

        if project_types:
            lines.append(f"نوع المشروع المكتشف: {', '.join(project_types)}")
        else:
            lines.append("لم يتم اكتشاف نوع مشروع معروف (قد يكون مجلد عام).")

        if key_files:
            lines.append(f"ملفات رئيسية موجودة: {', '.join(key_files)}")

        if git_info:
            branch = git_info.get("branch", "غير معروف")
            changes = git_info.get("uncommitted_changes", "0")
            lines.append(f"Git branch: {branch} | تغييرات غير محفوظة: {changes}")

        return "\n".join(lines)

    def should_refresh(self, last_root: Optional[str], current_root: str) -> bool:
        """يحدد هل السياق المحفوظ لسه صالح أو المستخدم غيّر مجلد العمل."""
        return last_root != current_root
