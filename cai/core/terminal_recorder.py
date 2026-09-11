"""
Terminal Recorder
-------------------
يسجّل جلسة Terminal كاملة (كل الأوامر والمخرجات بترتيبها الزمني) في ملف
نصي واحد قابل للمراجعة أو المشاركة لاحقًا — مفيد للتوثيق، مراجعة الأداء،
أو مشاركة "كيف حليت المشكلة دي" مع فريق العمل.

بعكس History (اللي بيحفظ الأوامر بس) و Session (بيانات meta)، الـ Recorder
ده بيحفظ كل حاجة اتطبعت فعليًا على الشاشة بالترتيب.
"""

import os
import time
from pathlib import Path
from typing import Optional


class TerminalRecorder:
    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai/recordings"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._active_file = None
        self._recording_name: Optional[str] = None

    @property
    def is_recording(self) -> bool:
        return self._active_file is not None

    def start(self, name: Optional[str] = None) -> str:
        if self.is_recording:
            return f"يوجد تسجيل نشط بالفعل: {self._recording_name}"

        name = name or time.strftime("session_%Y%m%d_%H%M%S")
        path = self.base_dir / f"{name}.log"
        self._active_file = open(path, "w", encoding="utf-8")
        self._recording_name = name
        self._active_file.write(f"=== بداية التسجيل: {time.ctime()} ===\n\n")
        return f"🔴 بدأ التسجيل: {name}"

    def write_input(self, text: str) -> None:
        if self.is_recording:
            self._active_file.write(f"cai > {text}\n")

    def write_output(self, text: str) -> None:
        if self.is_recording:
            self._active_file.write(f"{text}\n")

    def stop(self) -> str:
        if not self.is_recording:
            return "لا يوجد تسجيل نشط حاليًا."

        self._active_file.write(f"\n=== نهاية التسجيل: {time.ctime()} ===\n")
        self._active_file.close()
        name = self._recording_name
        self._active_file = None
        self._recording_name = None
        return f"⏹️ تم إيقاف التسجيل وحفظه: {name}.log"

    def list_recordings(self) -> list:
        return sorted(p.stem for p in self.base_dir.glob("*.log"))

    def read_recording(self, name: str) -> Optional[str]:
        path = self.base_dir / f"{name}.log"
        if not path.exists():
            return None
        return path.read_text(encoding="utf-8")
