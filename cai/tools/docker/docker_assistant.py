"""
Docker Assistant
----------------
يوفر واجهة مبسطة لعمليات Docker الشائعة: images, containers, compose, logs, exec.
"""

import shlex
from typing import Optional

from cai.engine.execution_engine import ExecutionEngine, ExecutionResult


class DockerAssistant:
    def __init__(self, engine: ExecutionEngine):
        self.engine = engine

    def _run(self, args: str, cwd: Optional[str] = None) -> ExecutionResult:
        return self.engine.run(f"docker {args}", cwd=cwd)

    # ---------- Images ----------

    def list_images(self) -> ExecutionResult:
        return self._run("images")

    def build_image(self, tag: str, context: str = ".", dockerfile: Optional[str] = None) -> ExecutionResult:
        args = f"build -t {shlex.quote(tag)}"
        if dockerfile:
            args += f" -f {shlex.quote(dockerfile)}"
        args += f" {shlex.quote(context)}"
        return self._run(args)

    def pull_image(self, image: str) -> ExecutionResult:
        return self._run(f"pull {shlex.quote(image)}")

    def remove_image(self, image: str) -> ExecutionResult:
        return self._run(f"rmi {shlex.quote(image)}")

    # ---------- Containers ----------

    def list_containers(self, all_containers: bool = True) -> ExecutionResult:
        args = "ps -a" if all_containers else "ps"
        return self._run(args)

    def run_container(self, image: str, name: Optional[str] = None,
                       ports: Optional[str] = None, detach: bool = True,
                       extra_args: str = "") -> ExecutionResult:
        args = "run"
        if detach:
            args += " -d"
        if name:
            args += f" --name {shlex.quote(name)}"
        if ports:
            args += f" -p {ports}"
        if extra_args:
            args += f" {extra_args}"
        args += f" {shlex.quote(image)}"
        return self._run(args)

    def stop_container(self, name_or_id: str) -> ExecutionResult:
        return self._run(f"stop {shlex.quote(name_or_id)}")

    def start_container(self, name_or_id: str) -> ExecutionResult:
        return self._run(f"start {shlex.quote(name_or_id)}")

    def remove_container(self, name_or_id: str, force: bool = False) -> ExecutionResult:
        args = "rm"
        if force:
            args += " -f"
        args += f" {shlex.quote(name_or_id)}"
        return self._run(args)

    def exec_in_container(self, name_or_id: str, command: str, interactive: bool = False) -> ExecutionResult:
        flag = "-it" if interactive else "-i"
        return self._run(f"exec {flag} {shlex.quote(name_or_id)} {command}")

    def logs(self, name_or_id: str, tail: int = 100) -> ExecutionResult:
        return self._run(f"logs --tail {tail} {shlex.quote(name_or_id)}")

    # ---------- Compose ----------

    def compose_up(self, cwd: Optional[str] = None, detach: bool = True) -> ExecutionResult:
        args = "compose up"
        if detach:
            args += " -d"
        return self.engine.run(f"docker {args}", cwd=cwd)

    def compose_down(self, cwd: Optional[str] = None) -> ExecutionResult:
        return self.engine.run("docker compose down", cwd=cwd)

    def compose_logs(self, cwd: Optional[str] = None) -> ExecutionResult:
        return self.engine.run("docker compose logs --tail 100", cwd=cwd)

    def system_prune(self, all_images: bool = False) -> ExecutionResult:
        args = "system prune -f"
        if all_images:
            args += " -a"
        return self._run(args)
