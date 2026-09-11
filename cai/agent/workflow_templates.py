"""
Workflow Templates
--------------------
قوالب جاهزة لمهام تطوير شائعة (بدل ما الـ AI يخطط من الصفر كل مرة).
كل Template بيرجع خطوات (شبه Plan جاهزة) ممكن تتنفذ مباشرة أو تتعدل.

الهدف: تسريع أكتر المهام تكرارًا (إنشاء مشروع Flask/React/بيئة Python...)
وتوفير استهلاك الـ AI في حالات معروفة النمط.
"""

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional


@dataclass
class TemplateStep:
    description: str
    command: Optional[str] = None


@dataclass
class WorkflowTemplate:
    key: str
    title: str
    description: str
    steps: List[TemplateStep]


def _flask_api_template() -> WorkflowTemplate:
    return WorkflowTemplate(
        key="flask-api",
        title="Flask REST API",
        description="مشروع Flask API جاهز مع بيئة افتراضية وهيكل أساسي.",
        steps=[
            TemplateStep("إنشاء مجلد المشروع", "mkdir -p {project_name}"),
            TemplateStep("إنشاء بيئة افتراضية", "python3 -m venv {project_name}/venv"),
            TemplateStep(
                "تثبيت Flask",
                "{project_name}/venv/bin/pip install flask flask-cors python-dotenv",
            ),
            TemplateStep(
                "إنشاء ملف app.py الأساسي",
                "cat > {project_name}/app.py << 'EOF'\n"
                "from flask import Flask, jsonify\n\n"
                "app = Flask(__name__)\n\n"
                "@app.route('/health')\n"
                "def health():\n"
                "    return jsonify({'status': 'ok'})\n\n"
                "if __name__ == '__main__':\n"
                "    app.run(debug=True, port=5000)\n"
                "EOF",
            ),
            TemplateStep("إنشاء requirements.txt", "{project_name}/venv/bin/pip freeze > {project_name}/requirements.txt"),
            TemplateStep("تشغيل السيرفر (اختياري، يدوي)", None),
        ],
    )


def _react_app_template() -> WorkflowTemplate:
    return WorkflowTemplate(
        key="react-app",
        title="React App (Vite)",
        description="تطبيق React جاهز عبر Vite.",
        steps=[
            TemplateStep("إنشاء مشروع React عبر Vite", "npm create vite@latest {project_name} -- --template react"),
            TemplateStep("الدخول للمجلد وتثبيت الحزم", "cd {project_name} && npm install"),
            TemplateStep("تشغيل السيرفر (اختياري، يدوي)", None),
        ],
    )


def _python_cli_template() -> WorkflowTemplate:
    return WorkflowTemplate(
        key="python-cli",
        title="Python CLI Tool",
        description="أداة سطر أوامر بايثون بسيطة مع argparse.",
        steps=[
            TemplateStep("إنشاء مجلد المشروع", "mkdir -p {project_name}"),
            TemplateStep(
                "إنشاء main.py الأساسي",
                "cat > {project_name}/main.py << 'EOF'\n"
                "import argparse\n\n"
                "def main():\n"
                "    parser = argparse.ArgumentParser(description='{project_name}')\n"
                "    parser.add_argument('--name', default='world')\n"
                "    args = parser.parse_args()\n"
                "    print(f'Hello, {args.name}!')\n\n"
                "if __name__ == '__main__':\n"
                "    main()\n"
                "EOF",
            ),
            TemplateStep("اختبار تشغيل الأداة", "python3 {project_name}/main.py --name cai"),
        ],
    )


def _dockerized_service_template() -> WorkflowTemplate:
    return WorkflowTemplate(
        key="docker-service",
        title="Dockerized Service",
        description="تجهيز Dockerfile وdocker-compose أساسيين لمشروع موجود.",
        steps=[
            TemplateStep(
                "إنشاء Dockerfile",
                "cat > Dockerfile << 'EOF'\n"
                "FROM python:3.11-slim\n"
                "WORKDIR /app\n"
                "COPY requirements.txt .\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n"
                "COPY . .\n"
                "CMD [\"python\", \"app.py\"]\n"
                "EOF",
            ),
            TemplateStep(
                "إنشاء docker-compose.yml",
                "cat > docker-compose.yml << 'EOF'\n"
                "services:\n"
                "  app:\n"
                "    build: .\n"
                "    ports:\n"
                "      - \"5000:5000\"\n"
                "EOF",
            ),
            TemplateStep("بناء الصورة", "docker compose build"),
        ],
    )


def _git_init_template() -> WorkflowTemplate:
    return WorkflowTemplate(
        key="git-init",
        title="Git Repository Setup",
        description="تهيئة مستودع Git جديد مع .gitignore أساسي وأول Commit.",
        steps=[
            TemplateStep("تهيئة المستودع", "git init"),
            TemplateStep(
                "إنشاء .gitignore",
                "cat > .gitignore << 'EOF'\n__pycache__/\n*.pyc\n.env\nvenv/\nnode_modules/\nEOF",
            ),
            TemplateStep("أول Commit", "git add -A && git commit -m 'Initial commit'"),
        ],
    )


TEMPLATES: Dict[str, Callable[[], WorkflowTemplate]] = {
    "flask-api": _flask_api_template,
    "react-app": _react_app_template,
    "python-cli": _python_cli_template,
    "docker-service": _dockerized_service_template,
    "git-init": _git_init_template,
}


class WorkflowTemplateManager:
    def list_templates(self) -> List[str]:
        return list(TEMPLATES.keys())

    def get(self, key: str, project_name: str = "my_project") -> Optional[WorkflowTemplate]:
        builder = TEMPLATES.get(key)
        if not builder:
            return None
        template = builder()
        for step in template.steps:
            if step.command:
                step.command = step.command.replace("{project_name}", project_name)
        return template

    def describe_all(self) -> str:
        lines = ["القوالب المتاحة:"]
        for key, builder in TEMPLATES.items():
            t = builder()
            lines.append(f"  {key:<16} — {t.description}")
        return "\n".join(lines)
