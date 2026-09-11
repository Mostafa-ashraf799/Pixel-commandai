"""
Execution Engine
----------------
مسؤول عن التنفيذ الفعلي لأوامر النظام، وقراءة:
- stdout
- stderr
- exit code

وبعد كل تنفيذ، يمرر النتيجة لباقي النظام (Agent) عشان يقرر الخطوة الجاية.
يمر أي أمر أولاً عبر PermissionManager قبل التنفيذ.
"""

import platform
import subprocess
from dataclasses import dataclass
from typing import Optional

from cai.security.permission_manager import PermissionManager, RiskLevel


@dataclass
class ExecutionResult:
    command: str
    stdout: str
    stderr: str
    exit_code: int
    success: bool
    risk: RiskLevel
    was_blocked: bool = False
    block_reason: Optional[str] = None


class ExecutionEngine:
    def __init__(self, permission_manager: PermissionManager, confirm_callback=None):
        """
        confirm_callback: دالة تستقبل (command, risk, explanation) وترجع True/False
        بتُستدعى لما الأمر يحتاج تأكيد من المستخدم (بيمررها الـ UI/Shell).
        """
        self.permissions = permission_manager
        self.confirm_callback = confirm_callback
        self.os_name = platform.system()  # Linux / Windows / Darwin

    def _get_shell_command(self, command: str):
        if self.os_name == "Windows":
            return ["powershell", "-NoProfile", "-Command", command]
        return ["/bin/bash", "-c", command]

    def run(self, command: str, cwd: Optional[str] = None, timeout: int = 120) -> ExecutionResult:
        needs_confirm, risk = self.permissions.requires_confirmation(command)

        if needs_confirm:
            explanation = self.permissions.explain_risk(risk)
            approved = True
            if self.confirm_callback:
                approved = self.confirm_callback(command, risk, explanation)
            if not approved:
                return ExecutionResult(
                    command=command, stdout="", stderr="",
                    exit_code=-1, success=False, risk=risk,
                    was_blocked=True, block_reason="تم الرفض من المستخدم.",
                )

        try:
            proc = subprocess.run(
                self._get_shell_command(command),
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return ExecutionResult(
                command=command,
                stdout=proc.stdout,
                stderr=proc.stderr,
                exit_code=proc.returncode,
                success=proc.returncode == 0,
                risk=risk,
            )
        except subprocess.TimeoutExpired:
            return ExecutionResult(
                command=command, stdout="", stderr="انتهت المهلة الزمنية للتنفيذ (timeout).",
                exit_code=-1, success=False, risk=risk,
            )
        except Exception as e:
            return ExecutionResult(
                command=command, stdout="", stderr=str(e),
                exit_code=-1, success=False, risk=risk,
            )

    def analyze_result(self, result: ExecutionResult) -> str:
        """تحليل مبسّط للنتيجة، يُستخدم كسياق يُرسل للـ AI لتحليل أعمق."""
        if result.was_blocked:
            return f"لم يتم تنفيذ الأمر: {result.block_reason}"
        if result.success:
            return f"تم تنفيذ الأمر بنجاح (exit code 0)."
        return (
            f"فشل تنفيذ الأمر (exit code {result.exit_code}).\n"
            f"رسالة الخطأ:\n{result.stderr.strip()[:2000]}"
        )
