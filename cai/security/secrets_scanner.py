"""
Secrets Scanner
-----------------
ميزة حماية مهمة جدًا لمستخدم بيبني مشاريع كتير: كشف مفاتيح API ومعلومات
حساسة اتنسيت مكتوبة صريح في الكود (Hardcoded)، قبل ما يعملها commit/push
عن طريق الغلط ويسرّبها على GitHub.

يفحص أنماط معروفة لمفاتيح شائعة (OpenAI, AWS, Google, GitHub, Stripe...)
بالإضافة لأنماط عامة (password=, secret=, api_key=...).
"""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List


IGNORED_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", "dist", "build"}

# كل نمط: (اسم وصفي, regex)
SECRET_PATTERNS = [
    ("OpenAI API Key", r"sk-[a-zA-Z0-9]{20,}"),
    ("Anthropic API Key", r"sk-ant-[a-zA-Z0-9\-_]{20,}"),
    ("Google API Key", r"AIza[0-9A-Za-z\-_]{35}"),
    ("AWS Access Key ID", r"AKIA[0-9A-Z]{16}"),
    ("GitHub Token", r"gh[pousr]_[A-Za-z0-9]{36,}"),
    ("Stripe Key", r"sk_live_[0-9a-zA-Z]{24,}"),
    ("Slack Token", r"xox[baprs]-[0-9a-zA-Z\-]{10,}"),
    ("Generic Private Key Block", r"-----BEGIN (RSA|EC|OPENSSH|PGP) PRIVATE KEY-----"),
    ("Hardcoded Password Assignment", r"(?i)\bpassword\s*=\s*[\"'][^\"']{4,}[\"']"),
    ("Hardcoded Secret Assignment", r"(?i)\b(secret|api_key|apikey|token)\s*=\s*[\"'][^\"']{8,}[\"']"),
]

TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".env", ".yml", ".yaml",
    ".txt", ".md", ".sh", ".ps1", ".php", ".rb", ".go", ".java", ".html",
}


@dataclass
class SecretFinding:
    file: str
    line_number: int
    pattern_name: str
    preview: str


class SecretsScanner:
    def scan_file(self, file_path: Path) -> List[SecretFinding]:
        findings = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except (OSError, UnicodeDecodeError):
            return findings

        for line_no, line in enumerate(content.splitlines(), start=1):
            for pattern_name, pattern in SECRET_PATTERNS:
                if re.search(pattern, line):
                    preview = line.strip()
                    if len(preview) > 100:
                        preview = preview[:100] + "..."
                    # إخفاء جزئي للقيمة المكتشفة في المعاينة نفسها
                    preview = self._mask_secret_in_preview(preview)
                    findings.append(SecretFinding(
                        file=str(file_path), line_number=line_no,
                        pattern_name=pattern_name, preview=preview,
                    ))
        return findings

    def _mask_secret_in_preview(self, text: str) -> str:
        def mask(match):
            value = match.group(0)
            if len(value) <= 8:
                return "*" * len(value)
            return value[:4] + "*" * (len(value) - 8) + value[-4:]

        for _, pattern in SECRET_PATTERNS:
            text = re.sub(pattern, mask, text)
        return text

    def scan_directory(self, root: str = ".", max_files: int = 2000) -> List[SecretFinding]:
        root_path = Path(root)
        all_findings = []
        scanned = 0

        for file_path in root_path.rglob("*"):
            if scanned >= max_files:
                break
            if any(part in IGNORED_DIRS for part in file_path.parts):
                continue
            if not file_path.is_file():
                continue
            if file_path.suffix not in TEXT_EXTENSIONS and file_path.name != ".env":
                continue

            scanned += 1
            all_findings.extend(self.scan_file(file_path))

        return all_findings

    def render_report(self, root: str = ".") -> str:
        findings = self.scan_directory(root)
        if not findings:
            return "✅ لم يتم العثور على أي أسرار أو مفاتيح مكشوفة في المشروع."

        lines = [f"🚨 تم العثور على {len(findings)} مشكلة محتملة:\n"]
        for f in findings:
            try:
                rel_path = str(Path(f.file).relative_to(Path(root).resolve()))
            except ValueError:
                rel_path = f.file
            lines.append(f"  [{f.pattern_name}] {rel_path}:{f.line_number}")
            lines.append(f"    {f.preview}")
        lines.append("\n💡 نصيحة: انقل القيم دي لملف .env وأضفه لـ .gitignore فورًا.")
        return "\n".join(lines)
