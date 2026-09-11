"""
Pre-Deploy Health Check
--------------------------
فحص شامل للمشروع قبل ما تنشره، بيجمع كذا فحص في تقرير واحد:
- Secrets Scanner (مفاتيح متسربة).
- ملفات أساسية ناقصة (README, .gitignore, requirements).
- حالة Git (تغييرات غير محفوظة، هل فيه remote مضبوط).
- ملفات ضخمة مش المفروض تتنشر.

الهدف: أمر واحد (`predeploy` أو `health`) يديك خلاصة "جاهز للنشر ولا لأ".
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from cai.security.secrets_scanner import SecretsScanner
from cai.tools.project_analyzer import ProjectAnalyzer
from cai.engine.execution_engine import ExecutionEngine


@dataclass
class HealthCheckResult:
    passed: bool = True
    critical_issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)


class PreDeployHealthCheck:
    def __init__(self, engine: ExecutionEngine, analyzer: Optional[ProjectAnalyzer] = None):
        self.engine = engine
        self.analyzer = analyzer
        self.scanner = SecretsScanner()

    def run(self, root: str = ".") -> HealthCheckResult:
        result = HealthCheckResult()
        root_path = Path(root)

        # 1. فحص الأسرار المتسربة (حرج)
        secrets = self.scanner.scan_directory(root)
        if secrets:
            result.passed = False
            result.critical_issues.append(
                f"🚨 تم اكتشاف {len(secrets)} مفتاح/سر مكشوف في الكود — يجب إصلاحه قبل النشر."
            )

        # 2. ملفات أساسية
        if not any(root_path.glob("README*")):
            result.warnings.append("لا يوجد ملف README.")

        has_py = any(root_path.rglob("*.py"))
        if has_py and not (root_path / "requirements.txt").exists() and not (root_path / "pyproject.toml").exists():
            result.warnings.append("مشروع بايثون بدون requirements.txt.")

        if (root_path / ".git").exists() and not (root_path / ".gitignore").exists():
            result.warnings.append("لا يوجد .gitignore رغم استخدام Git.")

        # 3. فحص .env مرفوع بالغلط
        gitignore_path = root_path / ".gitignore"
        env_path = root_path / ".env"
        if env_path.exists():
            gitignore_content = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
            if ".env" not in gitignore_content:
                result.passed = False
                result.critical_issues.append("ملف .env موجود لكنه غير مُستثنى في .gitignore — خطر تسريب فعلي.")

        # 4. حالة Git
        if (root_path / ".git").exists():
            status_result = self.engine.run("git status --porcelain", cwd=root)
            if status_result.success:
                changes = [l for l in status_result.stdout.splitlines() if l.strip()]
                if changes:
                    result.info.append(f"يوجد {len(changes)} تغيير غير محفوظ (uncommitted).")

            remote_result = self.engine.run("git remote -v", cwd=root)
            if remote_result.success and not remote_result.stdout.strip():
                result.warnings.append("لا يوجد remote مضبوط لهذا المستودع.")

        # 5. ملفات ضخمة
        for file in root_path.rglob("*"):
            if file.is_file() and ".git" not in file.parts:
                try:
                    if file.stat().st_size > 20 * 1024 * 1024:  # 20MB
                        result.warnings.append(f"ملف ضخم جدًا للنشر: {file.relative_to(root_path)}")
                except OSError:
                    pass

        return result

    def render_report(self, root: str = ".") -> str:
        result = self.run(root)

        lines = ["── Pre-Deploy Health Check ─────────"]

        if result.critical_issues:
            lines.append("\n🚨 مشاكل حرجة (يجب حلها قبل النشر):")
            lines.extend(f"  - {issue}" for issue in result.critical_issues)

        if result.warnings:
            lines.append("\n⚠️ تحذيرات (يُفضّل حلها):")
            lines.extend(f"  - {w}" for w in result.warnings)

        if result.info:
            lines.append("\nℹ️ معلومات:")
            lines.extend(f"  - {i}" for i in result.info)

        lines.append("")
        lines.append("✅ جاهز للنشر." if result.passed else "❌ غير جاهز للنشر — يوجد مشاكل حرجة.")

        return "\n".join(lines)
