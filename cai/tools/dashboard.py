"""
Dashboard
---------
يعرض حالة النظام اللحظية: CPU, RAM, Disk, Battery, Processes, Network.
يعتمد على مكتبة psutil (اختيارية) — لو غير متاحة، يرجع رسالة توضيحية
بدل الانهيار، عشان البرنامج يفضل شغال حتى بدون هذه الميزة.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False


@dataclass
class SystemSnapshot:
    cpu_percent: float = 0.0
    ram_percent: float = 0.0
    ram_used_gb: float = 0.0
    ram_total_gb: float = 0.0
    disk_percent: float = 0.0
    disk_used_gb: float = 0.0
    disk_total_gb: float = 0.0
    battery_percent: Optional[float] = None
    battery_plugged: Optional[bool] = None
    top_processes: List[Dict] = field(default_factory=list)
    available: bool = True
    error: Optional[str] = None


class Dashboard:
    def snapshot(self) -> SystemSnapshot:
        if not _HAS_PSUTIL:
            return SystemSnapshot(
                available=False,
                error="مكتبة psutil غير مثبتة. ثبّتها عبر: pip install psutil",
            )

        cpu = psutil.cpu_percent(interval=0.3)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        battery_percent = None
        battery_plugged = None
        try:
            battery = psutil.sensors_battery()
            if battery:
                battery_percent = battery.percent
                battery_plugged = battery.power_plugged
        except Exception:
            pass

        processes = []
        for p in sorted(
            psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]),
            key=lambda p: p.info.get("cpu_percent") or 0,
            reverse=True,
        )[:5]:
            processes.append(p.info)

        return SystemSnapshot(
            cpu_percent=cpu,
            ram_percent=mem.percent,
            ram_used_gb=round(mem.used / (1024 ** 3), 2),
            ram_total_gb=round(mem.total / (1024 ** 3), 2),
            disk_percent=disk.percent,
            disk_used_gb=round(disk.used / (1024 ** 3), 2),
            disk_total_gb=round(disk.total / (1024 ** 3), 2),
            battery_percent=battery_percent,
            battery_plugged=battery_plugged,
            top_processes=processes,
        )

    def render(self) -> str:
        snap = self.snapshot()
        if not snap.available:
            return f"⚠️ {snap.error}"

        lines = [
            "── Dashboard ─────────────────────",
            f"CPU     : {snap.cpu_percent}%",
            f"RAM     : {snap.ram_percent}%  ({snap.ram_used_gb}GB / {snap.ram_total_gb}GB)",
            f"Disk    : {snap.disk_percent}%  ({snap.disk_used_gb}GB / {snap.disk_total_gb}GB)",
        ]
        if snap.battery_percent is not None:
            plug_status = "⚡ متصل" if snap.battery_plugged else "🔋 بطارية"
            lines.append(f"Battery : {snap.battery_percent}% ({plug_status})")

        lines.append("")
        lines.append("Top Processes (by CPU):")
        for p in snap.top_processes:
            lines.append(f"  PID {p['pid']:<7} {p['name']:<25} CPU: {p.get('cpu_percent', 0)}%")

        return "\n".join(lines)
