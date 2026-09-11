"""
Background Jobs
------------------
نظام تشغيل أوامر في الخلفية زي Bash (jobs, fg, bg, kill)، مفيد للأوامر
طويلة المدى (سيرفر تطوير، مراقبة logs، بناء مشروع كبير) بدل ما تجمّد
جلسة cai بالكامل لحد ما الأمر يخلص.

يعتمد على subprocess.Popen غير المحجوب (non-blocking) بدل subprocess.run.
"""

import os
import signal
import subprocess
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Job:
    id: int
    command: str
    process: subprocess.Popen
    started_at: float = field(default_factory=time.time)
    status: str = "running"  # running | stopped | done | killed
    _stdout_lines: List[str] = field(default_factory=list)


class JobManager:
    def __init__(self):
        self._jobs: Dict[int, Job] = {}
        self._next_id = 1

    def start(self, command: str, cwd: Optional[str] = None) -> Job:
        process = subprocess.Popen(
            ["/bin/bash", "-c", command],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            preexec_fn=os.setsid,  # يسمح بقتل المجموعة كاملة عند الحاجة
        )
        job = Job(id=self._next_id, command=command, process=process)
        self._jobs[job.id] = job
        self._next_id += 1
        return job

    def _refresh_status(self, job: Job) -> None:
        if job.status in ("killed", "stopped"):
            return
        exit_code = job.process.poll()
        job.status = "done" if exit_code is not None else "running"

    def list_jobs(self) -> List[Job]:
        for job in self._jobs.values():
            self._refresh_status(job)
        return list(self._jobs.values())

    def get(self, job_id: int) -> Optional[Job]:
        job = self._jobs.get(job_id)
        if job:
            self._refresh_status(job)
        return job

    def bring_to_foreground(self, job_id: int, timeout: Optional[int] = None) -> str:
        """ينتظر انتهاء job معين ويرجع مخرجاته (fg)."""
        job = self.get(job_id)
        if not job:
            return f"لا توجد job بهذا الرقم: {job_id}"

        try:
            stdout, _ = job.process.communicate(timeout=timeout)
            job.status = "done"
            return stdout or "(بدون مخرجات)"
        except subprocess.TimeoutExpired:
            return f"لا تزال Job #{job_id} قيد التشغيل (timeout أثناء الانتظار)."

    def send_to_background(self, job_id: int) -> str:
        """تأكيد أن job معينة تعمل في الخلفية (bg) - أساسًا كل jobs هنا تبدأ في الخلفية فعليًا."""
        job = self.get(job_id)
        if not job:
            return f"لا توجد job بهذا الرقم: {job_id}"
        return f"Job #{job_id} تعمل في الخلفية: {job.command}"

    def kill(self, job_id: int) -> str:
        job = self._jobs.get(job_id)
        if not job:
            return f"لا توجد job بهذا الرقم: {job_id}"

        try:
            os.killpg(os.getpgid(job.process.pid), signal.SIGTERM)
            job.status = "killed"
            return f"تم إيقاف Job #{job_id} ({job.command})"
        except ProcessLookupError:
            job.status = "done"
            return f"Job #{job_id} كانت قد انتهت بالفعل."

    def render_list(self) -> str:
        jobs = self.list_jobs()
        if not jobs:
            return "لا توجد jobs نشطة."

        lines = ["Jobs:"]
        for job in jobs:
            elapsed = int(time.time() - job.started_at)
            lines.append(f"  [{job.id}] {job.status:<8} ({elapsed}s)  {job.command}")
        return "\n".join(lines)
