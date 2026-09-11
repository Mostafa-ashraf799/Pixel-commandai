"""
Project Analyzer
----------------
يحلل مشروعًا كاملاً: يعرض الهيكل، يكتشف مشاكل شائعة (ملفات ضخمة جدًا،
عدم وجود README/requirements، تكرار امتدادات مشبوهة)، ويستخدم الـ AI
لاقتراح تحسينات بناءً على ملخص الهيكل (وليس كل الأكواد لتفادي استهلاك مفرط).
"""

import os
from pathlib import Path
from typing import Dict, List

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage


IGNORED_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build", ".idea", ".vscode"}


class ProjectAnalyzer:
    def __init__(self, provider_manager: ProviderManager):
        self.provider_manager = provider_manager

    def build_tree(self, root: str, max_depth: int = 3) -> str:
        root_path = Path(root)
        lines = []

        def walk(path: Path, prefix: str, depth: int):
            if depth > max_depth:
                return
            try:
                entries = sorted(
                    [e for e in path.iterdir() if e.name not in IGNORED_DIRS and not e.name.startswith(".")],
                    key=lambda e: (e.is_file(), e.name.lower()),
                )
            except PermissionError:
                return
            for entry in entries:
                lines.append(f"{prefix}{entry.name}{'/' if entry.is_dir() else ''}")
                if entry.is_dir():
                    walk(entry, prefix + "  ", depth + 1)

        lines.append(f"{root_path.name}/")
        walk(root_path, "  ", 1)
        return "\n".join(lines)

    def detect_issues(self, root: str) -> List[str]:
        issues = []
        root_path = Path(root)

        has_readme = any(root_path.glob("README*"))
        if not has_readme:
            issues.append("لا يوجد ملف README في جذر المشروع.")

        has_py = any(root_path.rglob("*.py"))
        has_requirements = (root_path / "requirements.txt").exists() or (root_path / "pyproject.toml").exists()
        if has_py and not has_requirements:
            issues.append("مشروع بايثون بدون requirements.txt أو pyproject.toml.")

        has_js = any(root_path.rglob("*.js")) or any(root_path.rglob("*.ts"))
        has_package_json = (root_path / "package.json").exists()
        if has_js and not has_package_json:
            issues.append("مشروع JavaScript/TypeScript بدون package.json.")

        for file in root_path.rglob("*"):
            if file.is_file() and file.stat().st_size > 5 * 1024 * 1024:  # 5MB
                try:
                    issues.append(f"ملف كبير جدًا قد لا يجب أن يكون ضمن المشروع: {file.relative_to(root_path)}")
                except ValueError:
                    pass

        if not (root_path / ".gitignore").exists() and (root_path / ".git").exists():
            issues.append("لا يوجد ملف .gitignore رغم أن المشروع يستخدم Git.")

        return issues

    def summarize_stats(self, root: str) -> Dict[str, int]:
        root_path = Path(root)
        stats: Dict[str, int] = {}
        for file in root_path.rglob("*"):
            if file.is_file() and not any(part in IGNORED_DIRS for part in file.parts):
                ext = file.suffix or "(بدون امتداد)"
                stats[ext] = stats.get(ext, 0) + 1
        return dict(sorted(stats.items(), key=lambda x: -x[1]))

    def ai_suggestions(self, root: str) -> str:
        tree = self.build_tree(root)
        issues = self.detect_issues(root)
        stats = self.summarize_stats(root)

        summary = (
            f"هيكل المشروع:\n{tree}\n\n"
            f"إحصائيات الملفات:\n{stats}\n\n"
            f"مشاكل مكتشفة تلقائيًا:\n{issues}"
        )

        messages = [
            ChatMessage(
                role="system",
                content="أنت مهندس برمجيات خبير. حلل ملخص هيكل المشروع التالي واقترح "
                        "3 إلى 6 تحسينات عملية ومحددة (بنية، تنظيم، ملفات ناقصة، مخاطر).",
            ),
            ChatMessage(role="user", content=summary),
        ]
        response = self.provider_manager.chat(messages, temperature=0.3, max_tokens=1200)
        return response.content if response.ok else f"❌ خطأ: {response.error}"

    def full_report(self, root: str) -> str:
        tree = self.build_tree(root)
        issues = self.detect_issues(root)
        stats = self.summarize_stats(root)

        report = [f"تحليل المشروع: {root}", "", "الهيكل:", tree, ""]
        report.append("إحصائيات الملفات:")
        for ext, count in stats.items():
            report.append(f"  {ext}: {count}")
        report.append("")
        report.append("المشاكل المكتشفة:")
        if issues:
            report.extend(f"  ⚠️ {issue}" for issue in issues)
        else:
            report.append("  لا توجد مشاكل واضحة ✅")

        return "\n".join(report)
