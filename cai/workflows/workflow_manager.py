"""
Workflow System
------------------
أعمق من Workflow Templates الجاهزة (v2): هنا المستخدم يقدر يبني سير عمل
خاص بيه من الصفر، يحفظه، يشغّله لاحقًا، ويصدّره كملف JSON قابل للمشاركة
مع فريقه أو رفعه على GitHub كجزء من المشروع.

كل Workflow عبارة عن تسلسل خطوات، وكل خطوة إما:
- "shell"   : أمر Terminal مباشر.
- "ai"      : طلب نصي يُرسل للـ AI (بدون تنفيذ أوامر).
- "tool"    : استدعاء أداة مسجّلة في ToolRegistry مباشرة.
"""

import json
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional


@dataclass
class WorkflowStep:
    kind: str  # "shell" | "ai" | "tool"
    value: str  # الأمر أو الطلب أو اسم الأداة
    args: Dict[str, Any] = field(default_factory=dict)  # لخطوات "tool"


@dataclass
class Workflow:
    name: str
    description: str = ""
    steps: List[WorkflowStep] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "steps": [{"kind": s.kind, "value": s.value, "args": s.args} for s in self.steps],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Workflow":
        steps = [WorkflowStep(kind=s["kind"], value=s["value"], args=s.get("args", {})) for s in data.get("steps", [])]
        return cls(name=data["name"], description=data.get("description", ""), steps=steps,
                    created_at=data.get("created_at", time.time()))


class WorkflowManager:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or __import__("os").path.expanduser("~/.cai/workflows"))
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _path_for(self, name: str) -> Path:
        return self.base_dir / f"{name}.json"

    def create(self, name: str, description: str = "") -> Workflow:
        workflow = Workflow(name=name, description=description)
        self.save(workflow)
        return workflow

    def add_step(self, name: str, kind: str, value: str, args: Optional[Dict[str, Any]] = None) -> str:
        workflow = self.load(name)
        if not workflow:
            return f"سير العمل غير موجود: {name}. أنشئه أولاً عبر: workflow create {name}"
        workflow.steps.append(WorkflowStep(kind=kind, value=value, args=args or {}))
        self.save(workflow)
        return f"تمت إضافة خطوة ({kind}) لسير العمل '{name}'."

    def save(self, workflow: Workflow) -> None:
        with open(self._path_for(workflow.name), "w", encoding="utf-8") as f:
            json.dump(workflow.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self, name: str) -> Optional[Workflow]:
        path = self._path_for(name)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return Workflow.from_dict(json.load(f))

    def list_workflows(self) -> List[str]:
        return sorted(p.stem for p in self.base_dir.glob("*.json"))

    def delete(self, name: str) -> bool:
        path = self._path_for(name)
        if path.exists():
            path.unlink()
            return True
        return False

    def export(self, name: str, output_path: str) -> str:
        workflow = self.load(name)
        if not workflow:
            return f"سير العمل غير موجود: {name}"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(workflow.to_dict(), f, indent=2, ensure_ascii=False)
        return f"تم تصدير '{name}' إلى: {output_path}"

    def import_from(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        workflow = Workflow.from_dict(data)
        self.save(workflow)
        return f"تم استيراد سير العمل: {workflow.name}"

    def run(
        self,
        name: str,
        shell_runner: Callable[[str], str],
        ai_runner: Callable[[str], str],
        tool_runner: Callable[[str, dict], str],
        on_step: Optional[Callable[[int, WorkflowStep, str], None]] = None,
    ) -> List[str]:
        workflow = self.load(name)
        if not workflow:
            return [f"سير العمل غير موجود: {name}"]

        results = []
        for i, step in enumerate(workflow.steps, 1):
            if step.kind == "shell":
                output = shell_runner(step.value)
            elif step.kind == "ai":
                output = ai_runner(step.value)
            elif step.kind == "tool":
                output = tool_runner(step.value, step.args)
            else:
                output = f"نوع خطوة غير معروف: {step.kind}"

            results.append(output)
            if on_step:
                on_step(i, step, output)

        return results

    def render_details(self, name: str) -> str:
        workflow = self.load(name)
        if not workflow:
            return f"سير العمل غير موجود: {name}"

        lines = [f"Workflow: {workflow.name}", f"الوصف: {workflow.description}", "", "الخطوات:"]
        for i, step in enumerate(workflow.steps, 1):
            lines.append(f"  {i}. [{step.kind}] {step.value}")
        return "\n".join(lines)
