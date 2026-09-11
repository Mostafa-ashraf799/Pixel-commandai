"""
SSH Assistant
-------------
يدير الاتصالات البعيدة عبر SSH، نقل الملفات عبر SFTP/SCP، وتنفيذ أوامر بعيدة.
يعتمد على أدوات النظام (ssh, scp) المتاحة افتراضيًا في Linux/macOS،
وعلى OpenSSH في Windows الحديث.
"""

import shlex
from dataclasses import dataclass
from typing import Optional

from cai.engine.execution_engine import ExecutionEngine, ExecutionResult


@dataclass
class SSHTarget:
    host: str
    user: Optional[str] = None
    port: int = 22
    identity_file: Optional[str] = None

    def to_connection_string(self) -> str:
        return f"{self.user}@{self.host}" if self.user else self.host


class SSHAssistant:
    def __init__(self, engine: ExecutionEngine):
        self.engine = engine

    def _base_flags(self, target: SSHTarget) -> str:
        flags = f"-p {target.port}"
        if target.identity_file:
            flags += f" -i {shlex.quote(target.identity_file)}"
        return flags

    def connect_test(self, target: SSHTarget) -> ExecutionResult:
        """يختبر إمكانية الاتصال بدون فتح جلسة تفاعلية."""
        cmd = f"ssh {self._base_flags(target)} -o BatchMode=yes -o ConnectTimeout=5 {target.to_connection_string()} echo OK"
        return self.engine.run(cmd)

    def run_remote_command(self, target: SSHTarget, command: str) -> ExecutionResult:
        cmd = f"ssh {self._base_flags(target)} {target.to_connection_string()} {shlex.quote(command)}"
        return self.engine.run(cmd)

    def upload_file(self, target: SSHTarget, local_path: str, remote_path: str) -> ExecutionResult:
        cmd = (
            f"scp {self._base_flags(target)} {shlex.quote(local_path)} "
            f"{target.to_connection_string()}:{shlex.quote(remote_path)}"
        )
        return self.engine.run(cmd)

    def download_file(self, target: SSHTarget, remote_path: str, local_path: str) -> ExecutionResult:
        cmd = (
            f"scp {self._base_flags(target)} "
            f"{target.to_connection_string()}:{shlex.quote(remote_path)} {shlex.quote(local_path)}"
        )
        return self.engine.run(cmd)

    def sync_directory(self, target: SSHTarget, local_dir: str, remote_dir: str,
                        upload: bool = True) -> ExecutionResult:
        """مزامنة مجلد كامل عبر rsync إن كان متاحًا."""
        src = local_dir if upload else f"{target.to_connection_string()}:{remote_dir}"
        dst = f"{target.to_connection_string()}:{remote_dir}" if upload else local_dir
        cmd = f"rsync -avz -e 'ssh {self._base_flags(target)}' {shlex.quote(src)} {shlex.quote(dst)}"
        return self.engine.run(cmd)
