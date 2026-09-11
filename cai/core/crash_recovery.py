"""
Crash Recovery
----------------
لو cai وقع فجأة (استثناء غير متوقع، Segfault، إغلاق Terminal بالغلط)،
النظام ده بيسمح بالرجوع لآخر جلسة معروفة عند إعادة التشغيل، بدل ما
المستخدم يفقد سياق شغله بالكامل.

الفكرة بسيطة: كل جلسة بتكتب "heartbeat" دوري + آخر أمر اتنفذ في ملف
منفصل. لو cai اتقفل بشكل غير طبيعي (heartbeat قديم بدون end_session)،
عند التشغيل التالي بيتقرح استرجاع آخر جلسة.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional


class CrashRecoveryManager:
    STALE_THRESHOLD_SECONDS = 30  # لو آخر heartbeat أقدم من كده، نعتبرها جلسة متعطلة

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.state_path = self.base_dir / "crash_state.json"

    def heartbeat(self, session_id: str, last_command: str = "") -> None:
        data = {
            "session_id": session_id,
            "last_command": last_command,
            "ts": time.time(),
            "clean_exit": False,
        }
        with open(self.state_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def mark_clean_exit(self) -> None:
        if not self.state_path.exists():
            return
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["clean_exit"] = True
            with open(self.state_path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except (json.JSONDecodeError, OSError):
            pass

    def check_for_crash(self) -> Optional[dict]:
        """يُستدعى عند بداية تشغيل cai. يرجع بيانات الجلسة المتعطلة لو وُجدت."""
        if not self.state_path.exists():
            return None
        try:
            with open(self.state_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        if data.get("clean_exit"):
            return None  # آخر جلسة اتقفلت بشكل طبيعي، مفيش crash

        return data

    def render_recovery_prompt(self, crash_data: dict) -> str:
        session_id = crash_data.get("session_id", "unknown")
        last_command = crash_data.get("last_command", "")
        when = time.ctime(crash_data.get("ts", 0))
        return (
            f"⚠️ يبدو أن آخر جلسة (Session {session_id}) انتهت بشكل غير متوقع في {when}.\n"
            f"آخر أمر تم تنفيذه: {last_command or '(غير معروف)'}\n"
            f"استخدم 'session resume {session_id}' للعودة إليها، أو تجاهل هذه الرسالة للبدء من جديد."
        )
