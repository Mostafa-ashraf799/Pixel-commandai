"""
Git Assistant
-------------
يوفر واجهة مبسطة لعمليات Git الشائعة (clone, commit, push, pull, branch,
merge, resolve conflicts) عن طريق الـ ExecutionEngine، مع تفعيل نظام
الصلاحيات تلقائيًا (git push --force مصنف Dangerous مثلاً).
"""

import shlex
from typing import List, Optional

from cai.engine.execution_engine import ExecutionEngine, ExecutionResult


class GitAssistant:
    def __init__(self, engine: ExecutionEngine):
        self.engine = engine

    def _run(self, args: str, cwd: Optional[str] = None) -> ExecutionResult:
        return self.engine.run(f"git {args}", cwd=cwd)

    def status(self, cwd: Optional[str] = None) -> ExecutionResult:
        return self._run("status", cwd=cwd)

    def clone(self, repo_url: str, target_dir: Optional[str] = None) -> ExecutionResult:
        args = f"clone {shlex.quote(repo_url)}"
        if target_dir:
            args += f" {shlex.quote(target_dir)}"
        return self._run(args)

    def commit(self, message: str, add_all: bool = True, cwd: Optional[str] = None) -> List[ExecutionResult]:
        results = []
        if add_all:
            results.append(self._run("add -A", cwd=cwd))
        results.append(self._run(f"commit -m {shlex.quote(message)}", cwd=cwd))
        return results

    def push(self, remote: str = "origin", branch: Optional[str] = None,
              force: bool = False, cwd: Optional[str] = None) -> ExecutionResult:
        args = f"push {remote}"
        if branch:
            args += f" {branch}"
        if force:
            args += " --force"
        return self._run(args, cwd=cwd)

    def pull(self, remote: str = "origin", branch: Optional[str] = None,
             cwd: Optional[str] = None) -> ExecutionResult:
        args = f"pull {remote}"
        if branch:
            args += f" {branch}"
        return self._run(args, cwd=cwd)

    def create_branch(self, name: str, checkout: bool = True, cwd: Optional[str] = None) -> ExecutionResult:
        args = f"checkout -b {shlex.quote(name)}" if checkout else f"branch {shlex.quote(name)}"
        return self._run(args, cwd=cwd)

    def switch_branch(self, name: str, cwd: Optional[str] = None) -> ExecutionResult:
        return self._run(f"checkout {shlex.quote(name)}", cwd=cwd)

    def list_branches(self, cwd: Optional[str] = None) -> ExecutionResult:
        return self._run("branch -a", cwd=cwd)

    def merge(self, branch: str, cwd: Optional[str] = None) -> ExecutionResult:
        return self._run(f"merge {shlex.quote(branch)}", cwd=cwd)

    def diff(self, cwd: Optional[str] = None) -> ExecutionResult:
        return self._run("diff", cwd=cwd)

    def log(self, limit: int = 10, cwd: Optional[str] = None) -> ExecutionResult:
        return self._run(f"log --oneline -n {limit}", cwd=cwd)

    def has_conflicts(self, cwd: Optional[str] = None) -> bool:
        result = self._run("diff --name-only --diff-filter=U", cwd=cwd)
        return bool(result.stdout.strip())

    def conflict_files(self, cwd: Optional[str] = None) -> List[str]:
        result = self._run("diff --name-only --diff-filter=U", cwd=cwd)
        return [f for f in result.stdout.splitlines() if f.strip()]
