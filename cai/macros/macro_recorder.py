"""
Macro Recorder
----------------
يسجّل تسلسل أوامر المستخدم الفعلي أثناء الجلسة (بعكس Workflow اللي
بيتبني يدويًا)، ويسمح بحفظه كـ Macro وإعادة تشغيله بأمر واحد لاحقًا.

الفرق عن Workflow: الـ Macro بيتسجل "لايف" من استخدام حقيقي (record → stop
→ save)، بينما الـ Workflow بيتبني بخطوات مُعرَّفة صراحة من المستخدم.
"""

import json
import os
import time
from pathlib import Path
from typing import Callable, Dict, List, Optional


class MacroRecorder:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai/macros"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._recording: bool = False
        self._buffer: List[str] = []

    @property
    def is_recording(self) -> bool:
        return self._recording

    def start(self) -> str:
        if self._recording:
            return "التسجيل شغال بالفعل."
        self._recording = True
        self._buffer = []
        return "🔴 بدأ تسجيل الماكرو. كل أمر هيتسجل لحد ما تكتب: macro stop"

    def capture(self, command: str) -> None:
        """يُستدعى من CommandRouter لكل أمر أثناء التسجيل النشط."""
        if self._recording:
            self._buffer.append(command)

    def stop(self) -> List[str]:
        self._recording = False
        return list(self._buffer)

    def save(self, name: str, commands: Optional[List[str]] = None) -> str:
        commands = commands if commands is not None else self._buffer
        if not commands:
            return "لا توجد أوامر لحفظها كماكرو."

        path = self.base_dir / f"{name}.json"
        data = {"name": name, "commands": commands, "created_at": time.time()}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._buffer = []
        return f"تم حفظ الماكرو '{name}' ({len(commands)} أمر)."

    def load(self, name: str) -> Optional[List[str]]:
        path = self.base_dir / f"{name}.json"
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("commands", [])

    def run(self, name: str, executor: Callable[[str], None]) -> str:
        commands = self.load(name)
        if commands is None:
            return f"الماكرو غير موجود: {name}"

        for cmd in commands:
            executor(cmd)

        return f"تم تشغيل الماكرو '{name}' ({len(commands)} أمر)."

    def list_macros(self) -> List[str]:
        return sorted(p.stem for p in self.base_dir.glob("*.json"))

    def delete(self, name: str) -> bool:
        path = self.base_dir / f"{name}.json"
        if path.exists():
            path.unlink()
            return True
        return False

    def render_details(self, name: str) -> str:
        commands = self.load(name)
        if commands is None:
            return f"الماكرو غير موجود: {name}"
        lines = [f"Macro: {name} ({len(commands)} أمر)"]
        lines.extend(f"  {i}. {cmd}" for i, cmd in enumerate(commands, 1))
        return "\n".join(lines)
