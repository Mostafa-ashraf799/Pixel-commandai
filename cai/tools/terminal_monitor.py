"""
Terminal Monitor
-----------------
يراقب سلوك الجلسة الحالية: عدد الأخطاء المتكررة، الأوامر المنفذة،
واستهلاك الموارد وقت التنفيذ (عبر Dashboard). يُستخدم لرفع تنبيهات
استباقية (مثلاً: نفس الأمر فشل 3 مرات متتالية).
"""

from collections import Counter
from dataclasses import dataclass, field
from typing import List, Optional

from cai.tools.dashboard import Dashboard
from cai.engine.execution_engine import ExecutionResult


@dataclass
class MonitorEvent:
    command: str
    success: bool


class TerminalMonitor:
    def __init__(self, dashboard: Optional[Dashboard] = None, repeat_failure_threshold: int = 3):
        self.dashboard = dashboard or Dashboard()
        self.events: List[MonitorEvent] = []
        self.repeat_failure_threshold = repeat_failure_threshold

    def record(self, result: ExecutionResult) -> None:
        self.events.append(MonitorEvent(command=result.command, success=result.success))

    def failure_count_for(self, command: str) -> int:
        return sum(1 for e in self.events if e.command == command and not e.success)

    def is_repeating_failure(self, command: str) -> bool:
        return self.failure_count_for(command) >= self.repeat_failure_threshold

    def most_common_errors(self, top_n: int = 5) -> List[tuple]:
        failed_commands = [e.command for e in self.events if not e.success]
        return Counter(failed_commands).most_common(top_n)

    def success_rate(self) -> float:
        if not self.events:
            return 100.0
        successes = sum(1 for e in self.events if e.success)
        return round((successes / len(self.events)) * 100, 1)

    def resource_alert(self, cpu_threshold: float = 90.0, ram_threshold: float = 90.0) -> Optional[str]:
        snap = self.dashboard.snapshot()
        if not snap.available:
            return None
        alerts = []
        if snap.cpu_percent >= cpu_threshold:
            alerts.append(f"⚠️ استهلاك CPU مرتفع: {snap.cpu_percent}%")
        if snap.ram_percent >= ram_threshold:
            alerts.append(f"⚠️ استهلاك RAM مرتفع: {snap.ram_percent}%")
        return "\n".join(alerts) if alerts else None

    def summary(self) -> str:
        lines = [
            f"عدد الأوامر المنفذة: {len(self.events)}",
            f"نسبة النجاح: {self.success_rate()}%",
        ]
        common_errors = self.most_common_errors()
        if common_errors:
            lines.append("أكثر الأوامر فشلاً:")
            for cmd, count in common_errors:
                lines.append(f"  {cmd}  ({count} مرة)")
        return "\n".join(lines)
