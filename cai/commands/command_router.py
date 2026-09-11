"""
Command Router
--------------
موزع الأوامر المركزي. دلوقتي بياخد DI Container بدل تمرير كل خدمة
يدويًا، وبينشر أحداث EventBus بدل النداء المباشر على Logger/Session.
"""

import platform
import shlex
from pathlib import Path
from typing import Callable, Dict

from cai.core.di.container import Container
from cai.core.events.events import Events
from cai.providers.base_provider import ChatMessage

from cai.tools.git.git_assistant import GitAssistant
from cai.tools.docker.docker_assistant import DockerAssistant
from cai.tools.ssh.ssh_assistant import SSHAssistant, SSHTarget
from cai.tools.network.network_tools import NetworkTools
from cai.tools.package.package_manager import PackageManager
from cai.tools.files.file_manager import FileManager
from cai.tools.code_assistant import CodeAssistant
from cai.tools.project_analyzer import ProjectAnalyzer
from cai.tools.dashboard import Dashboard
from cai.tools.terminal_monitor import TerminalMonitor
from cai.tools.linux_engine import LinuxEngine
from cai.tools.windows_engine import WindowsEngine
from cai.plugins.plugin_manager import PluginManager
from cai.plugins.marketplace import PluginMarketplace
from cai.ui.theme_manager import ThemeManager

from cai.agent.multi_agent import MultiAgentTeam
from cai.agent.tool_calling_agent import ToolCallingAgent
from cai.tools.web_search import WebSearchTool
from cai.agent.workflow_templates import WorkflowTemplateManager
from cai.tools.script_generator import ScriptGenerator
from cai.core.auto_context import AutoContextEngine
from cai.core.context_manager import ContextManager
from cai.core.intent_router import IntentRouter
from cai.tools.voice_assistant import VoiceAssistant

from cai.core.snapshot_manager import SnapshotManager
from cai.security.secrets_scanner import SecretsScanner
from cai.tools.health_check import PreDeployHealthCheck
from cai.tools.doc_generator import DocGenerator
from cai.core.alias_manager import AliasManager
from cai.core.prompt_loader import PromptLoader

from cai.tools_registry.tool_registry import ToolRegistry
from cai.tools_registry.builtin_tools import register_builtin_tools
from cai.roles.ai_roles import RoleSelector
from cai.profiles.profile_manager import ProfileManager
from cai.memory.session_manager import SessionManager
from cai.jobs.job_manager import JobManager
from cai.workflows.workflow_manager import WorkflowManager
from cai.macros.macro_recorder import MacroRecorder
from cai.config.layered_config import LayeredConfig
from cai.core.error_database import ErrorDatabase
from cai.core.offline_mode import OfflineModeManager
from cai.core.telemetry import TelemetryManager

from cai.platform.platform_detector import get_platform_info
from cai.platform.termux_api import TermuxAPIBridge
from cai.platform.storage_access import StorageAccessManager
from cai.core.config_sync import ConfigSyncManager

from cai.cloud.auth_manager import AuthManager, AuthError
from cai.providers.provider_manager import PIXEL_SUPABASE_URL, PIXEL_SUPABASE_ANON_KEY


class CommandRouter:
    KNOWN_COMMANDS = [
        "help", "about", "status", "fix", "doc", "plan", "do", "run", "exp",
        "code", "edit", "dbg", "rev", "mk", "git", "docker", "ssh", "pkg",
        "net", "scan", "dash", "cfg", "mdl", "provider", "api", "plug", "theme", "log",
        "his", "mem", "session", "clear", "exit",
        "team", "search", "template", "script", "context", "voice",
        "cost", "snapshot", "undo", "secrets", "predeploy", "docgen", "alias",
        "agent", "role", "profile", "jobs", "fg", "bg", "kill",
        "workflow", "macro", "config", "errors", "offline", "telemetry",
        "doctor", "whoami", "metrics", "sync", "bench",
        "termux", "storage", "ollama", "phone",
        "login", "signup", "logout", "account", "upgrade",
    ]

    def __init__(self, container: Container, printer: Callable[[str], None] = print):
        self.container = container
        self.printer = printer
        self.os_name = platform.system()

        # ---------- خدمات أساسية من الـ Container ----------
        self.config = container.resolve("config")
        self.keys = container.resolve("keys")
        self.permissions = container.resolve("permissions")
        self.providers = container.resolve("providers")
        self.engine = container.resolve("engine")
        self.memory = container.resolve("memory")
        self.history = container.resolve("history")
        self.session = container.resolve("session")
        self.cost_tracker = container.resolve("cost_tracker")
        self.event_bus = container.resolve("event_bus")

        # ---------- أدوات v1/v2 (تُبنى مباشرة، ليست Singletons عامة) ----------
        self.git = GitAssistant(self.engine)
        self.docker = DockerAssistant(self.engine)
        self.ssh = SSHAssistant(self.engine)
        self.net = NetworkTools(self.engine)
        self.pkg = PackageManager(self.engine)
        self.files = FileManager()
        self.code = CodeAssistant(self.providers)
        self.analyzer = ProjectAnalyzer(self.providers)
        self.dashboard = Dashboard()
        self.monitor = TerminalMonitor(self.dashboard)
        self.linux_engine = LinuxEngine(self.providers, self.engine) if self.os_name != "Windows" else None
        self.windows_engine = WindowsEngine(self.providers, self.engine) if self.os_name == "Windows" else None
        self.plugins = PluginManager()
        self.marketplace = PluginMarketplace(self.plugins)
        self.theme = ThemeManager(self.config.get("theme", "dark"))

        # ---------- مميزات v2 ----------
        self.prompts = PromptLoader()
        self.multi_agent = MultiAgentTeam(self.providers, self.engine, self.prompts)
        self.web_search = WebSearchTool(self.providers)
        self.templates = WorkflowTemplateManager()
        self.script_gen = ScriptGenerator(self.providers)
        self.auto_context = AutoContextEngine(self.engine)
        self.intent_router = IntentRouter()
        self.voice = VoiceAssistant()
        self.snapshots = SnapshotManager()
        self.secrets_scanner = SecretsScanner()
        self.health_check = PreDeployHealthCheck(self.engine, self.analyzer)
        self.doc_generator = DocGenerator(self.providers)
        self.aliases = AliasManager()

        # ---------- مميزات v3 (الدفعة الحالية) ----------
        self.context_manager = ContextManager(self.engine, self.memory, self.history)
        self.tool_registry = ToolRegistry()
        register_builtin_tools(self.tool_registry, self.files, self.git, self.engine, self.net, self.dashboard)
        self.tool_agent = ToolCallingAgent(self.providers, self.tool_registry)
        self.role_selector = RoleSelector(self.providers, self.prompts)
        self.profiles = ProfileManager()
        self.jobs = JobManager()
        self.workflows = WorkflowManager()
        self.macros = MacroRecorder()
        self.layered_config = LayeredConfig(self.config)
        self.error_db = ErrorDatabase()
        self.offline_mode = OfflineModeManager(self.providers)
        self.telemetry = TelemetryManager(enabled=self.config.get("telemetry_enabled", False))

        # ---------- دعم Termux / Android ----------
        self.platform_info = get_platform_info()
        self.termux_api = TermuxAPIBridge()
        self.storage = StorageAccessManager(self.platform_info)
        self.config_sync = ConfigSyncManager(self.config, self.aliases)

        # ---------- Pixel CommandAI: حساب المستخدم والاشتراك ----------
        # نفس نسخة AuthManager اللي بيستخدمها PixelProvider، عشان تسجيل
        # الدخول من هنا يبقى فعّال فورًا للـ provider من غير أي إعادة تشغيل.
        self.pixel_auth: AuthManager = self.providers.pixel_auth

        self._last_error: str = ""
        self._last_error_fingerprint: str = ""

        self._dispatch_table: Dict[str, Callable[[str], None]] = {
            "help": self.cmd_help,
            "about": self.cmd_about,
            "status": self.cmd_status,
            "do": self.cmd_do,
            "plan": self.cmd_do,
            "run": self.cmd_run,
            "mdl": self.cmd_model,
            "provider": self.cmd_provider,
            "api": self.cmd_api,
            "cfg": self.cmd_config_legacy,
            "theme": self.cmd_theme,
            "mem": self.cmd_memory,
            "clear": self.cmd_clear,
            "exit": self.cmd_exit,
            "exp": self.cmd_explain,
            "fix": self.cmd_fix,
            "doc": self.cmd_diagnose,
            "code": self.cmd_code,
            "edit": self.cmd_edit,
            "dbg": self.cmd_debug,
            "rev": self.cmd_review,
            "mk": self.cmd_make_project,
            "git": self.cmd_git,
            "docker": self.cmd_docker,
            "ssh": self.cmd_ssh,
            "pkg": self.cmd_pkg,
            "net": self.cmd_net,
            "scan": self.cmd_scan,
            "dash": self.cmd_dashboard,
            "plug": self.cmd_plugins,
            "his": self.cmd_history,
            "session": self.cmd_session,
            "analyze": self.cmd_analyze,
            "team": self.cmd_team,
            "search": self.cmd_search,
            "template": self.cmd_template,
            "script": self.cmd_script,
            "context": self.cmd_context,
            "voice": self.cmd_voice,
            "cost": self.cmd_cost,
            "snapshot": self.cmd_snapshot,
            "undo": self.cmd_undo,
            "secrets": self.cmd_secrets,
            "predeploy": self.cmd_predeploy,
            "docgen": self.cmd_docgen,
            "alias": self.cmd_alias,
            # ---------- v3 ----------
            "agent": self.cmd_agent,
            "role": self.cmd_role,
            "profile": self.cmd_profile,
            "jobs": self.cmd_jobs,
            "fg": self.cmd_fg,
            "bg": self.cmd_bg,
            "kill": self.cmd_kill,
            "workflow": self.cmd_workflow,
            "macro": self.cmd_macro,
            "config": self.cmd_config,
            "errors": self.cmd_errors,
            "offline": self.cmd_offline,
            "telemetry": self.cmd_telemetry,
            "doctor": self.cmd_doctor,
            "whoami": self.cmd_whoami,
            "metrics": self.cmd_metrics,
            "termux": self.cmd_termux,
            "storage": self.cmd_storage,
            "ollama": self.cmd_ollama,
            "phone": self.cmd_phone,
            "sync": self.cmd_sync,
            "login": self.cmd_login,
            "signup": self.cmd_signup,
            "logout": self.cmd_logout,
            "account": self.cmd_account,
            "upgrade": self.cmd_upgrade,
        }

        self._should_exit = False

    @property
    def should_exit(self) -> bool:
        return self._should_exit

    # ---------- الحلقة الرئيسية للتوزيع ----------

    def handle(self, user_input: str) -> None:
        user_input = user_input.strip()
        if not user_input:
            return

        # الماكرو أثناء التسجيل النشط (يُسجَّل الأمر الخام قبل أي تفكيك)
        self.macros.capture(user_input)

        # فحص الاختصارات المخصصة (alias)
        expanded_commands = self.aliases.expand(user_input)
        if expanded_commands:
            for cmd in expanded_commands:
                self.handle(cmd)
            return

        parts = user_input.split(" ", 1)
        cmd_word = parts[0].lower()
        rest = parts[1] if len(parts) > 1 else ""

        self.memory.add_message("user", user_input)
        self.history.add(user_input)
        self.telemetry.record_command_usage(cmd_word)

        handler = self._dispatch_table.get(cmd_word)
        try:
            if handler:
                handler(rest)
                self._publish_command_executed(user_input, success=True)
            else:
                suggested = self.intent_router.suggest_command(user_input)
                if suggested:
                    suggested_word = suggested.split(" ", 1)[0]
                    suggested_rest = suggested.split(" ", 1)[1] if " " in suggested else ""
                    suggested_handler = self._dispatch_table.get(suggested_word)
                    if suggested_handler:
                        self.printer(f"↳ فهمت طلبك كـ: {suggested}")
                        suggested_handler(suggested_rest)
                        self._publish_command_executed(user_input, success=True)
                        return
                self.cmd_chat(user_input)
                self._publish_command_executed(user_input, success=True)
        except Exception as e:
            self._last_error = str(e)
            self._publish_command_executed(user_input, success=False)
            self.event_bus.publish(Events.ERROR_OCCURRED, command=user_input, error=str(e))
            self.printer(f"❌ خطأ أثناء تنفيذ الأمر: {e}")

    def _publish_command_executed(self, command: str, success: bool, risk: str = "safe") -> None:
        self.event_bus.publish(Events.COMMAND_EXECUTED, command=command, success=success, risk=risk)

    # ---------- أوامر عامة ----------

    def cmd_help(self, _: str) -> None:
        self.printer(
            "الأوامر الأساسية:\n"
            "  do <task>        تنفيذ مهمة كاملة بخطة تلقائية\n"
            "  agent <task>     Tool-Calling Agent حقيقي (ينادي أدوات فعلية)\n"
            "  team <task>      فريق Multi-Agent (Architect→Coder→Reviewer→Fixer)\n"
            "  role <name> <q>  اسأل دور AI متخصص (coder/reviewer/linux_expert/...)\n"
            "  run <cmd>        تنفيذ أمر Terminal مباشر\n"
            "  git/docker/ssh/pkg/net/scan  أدوات النظام\n"
            "  code/edit/dbg/rev/analyze    أدوات الكود\n"
            "  template/script/workflow/macro   أتمتة متقدمة\n"
            "  cost/snapshot/undo/secrets/predeploy/docgen   حماية وجودة\n"
            "  session/jobs/fg/bg/kill       إدارة الجلسات والمهام الخلفية\n"
            "  profile/theme/config/alias    تخصيص\n"
            "  doctor/whoami/metrics/errors  تشخيص\n"
            "  status/mem/his/clear/exit\n\n"
            "💡 تقدر تكتب طلبك بلغة طبيعية زي 'install docker' وهيتفهم تلقائيًا.\n"
            "اكتب 'help <أمر>' — قريبًا — أو راجع README لتفاصيل كل أمر."
        )
        if self.platform_info.is_termux:
            self.printer(
                "\n📱 أوامر خاصة بـ Termux:\n"
                "  termux [api]     معلومات المنصة / أدوات الهاتف\n"
                "  storage [name]   الوصول لتخزين الهاتف (downloads, dcim...)\n"
                "  phone <action>   تحكم سريع (battery, notify, vibrate, toast, clipboard, speak, location)\n"
                "  ollama status/connect   استخدام Ollama محليًا أو عن بُعد\n"
                "  sync export/import      مزامنة الإعدادات مع جهاز تاني"
            )

    def cmd_about(self, _: str) -> None:
        self.printer(f"CommandAI (cai) — الإصدار {self.config.get('version')} | Session: {self.session.session_id}")

    def cmd_status(self, _: str) -> None:
        status = self.providers.status()
        self.printer(
            f"Provider : {status['provider']}\n"
            f"Model    : {status['model']}\n"
            f"Mode     : {self.config.get('mode')}\n"
            f"Profile  : {self.profiles.active.display_name}\n"
            f"OS       : {self.os_name}\n"
            f"Configured: {'✅' if status['configured'] else '❌ (بدون API key)'}"
        )

    # ---------- Agent (Legacy Planner) ----------

    def cmd_do(self, task: str) -> None:
        if not task:
            self.printer("استخدم: do <وصف المهمة>")
            return

        from cai.agent.planner import Planner
        from cai.agent.agent_executor import AgentExecutor

        self.event_bus.publish(Events.TASK_STARTED, task=task)
        self.printer("جاري إنشاء الخطة...")

        planner = Planner(self.providers)
        plan = planner.create_plan(task)
        self.printer(plan.pretty_print())

        confirm = input("\nStart? [Y/n] ").strip().lower()
        if confirm not in ("", "y", "yes"):
            self.printer("تم الإلغاء.")
            self.event_bus.publish(Events.TASK_FINISHED, task=task, success=False)
            return

        executor = AgentExecutor(self.engine, self.providers)

        def on_start(step):
            self.printer(f"\n▶ تنفيذ: {step.description}")

        def on_done(step):
            status = "✔" if step.done else "✘"
            self.printer(f"{status} {step.result}")
            self.event_bus.publish(Events.TASK_STEP_DONE, step_description=step.description, success=step.done)

        executor.on_step_start = on_start
        executor.on_step_done = on_done
        executor.run_plan(plan)

        success = all(s.done for s in plan.steps)
        self.event_bus.publish(Events.TASK_FINISHED, task=task, success=success)

    # ---------- Tool-Calling Agent (v3، حقيقي) ----------

    def cmd_agent(self, task: str) -> None:
        if not task:
            self.printer("استخدم: agent <طلبك> — مثال: agent اقرأ ملف app.py وأخبرني بمشاكله")
            return

        context = self.context_manager.build_prompt_context()

        def confirm_tool(tool, arguments):
            self.printer(f"\n⚠️ الأداة '{tool.name}' تحتاج تأكيد (وسائط: {arguments})")
            answer = input("تنفيذ؟ [y/N] ").strip().lower()
            return answer in ("y", "yes")

        def on_tool_call(trace):
            status = "✔" if trace.success else "✘"
            self.printer(f"  {status} استدعاء أداة: {trace.tool_name}({trace.arguments}) → {trace.result_preview}")

        self.printer("🤖 الوكيل يعمل (Tool Calling)...")
        result = self.tool_agent.run(task, context=context, confirm_callback=confirm_tool, on_tool_call=on_tool_call)

        self.printer(f"\n{result.final_response}")
        if result.trace:
            self.printer(f"\n({len(result.trace)} استدعاء أداة عبر {result.rounds_used} جولة)")

    # ---------- AI Roles ----------

    def cmd_role(self, args: str) -> None:
        if not args:
            self.printer(f"الأدوار المتاحة: {', '.join(self.role_selector.list_roles())}")
            self.printer("استخدم: role <اسم الدور> <سؤالك> — أو: role auto <سؤالك>")
            return

        parts = args.split(" ", 1)
        role_key = parts[0]
        question = parts[1] if len(parts) > 1 else ""

        if not question:
            self.printer("استخدم: role <اسم الدور> <سؤالك>")
            return

        if role_key == "auto":
            role_name, answer = self.role_selector.ask_auto(question)
            self.printer(f"[تم اختيار الدور تلقائيًا: {role_name}]\n\n{answer}")
        else:
            self.printer(self.role_selector.ask_as(role_key, question))

    # ---------- Profiles ----------

    def cmd_profile(self, name: str) -> None:
        if not name:
            self.printer(self.profiles.render_list())
            return
        ok = self.profiles.set_active(name)
        if ok:
            self.config.set("mode", self.profiles.active.default_mode)
            self.permissions.set_mode(self.profiles.active.default_mode)
            self.printer(f"تم التحويل لبروفايل: {self.profiles.active.display_name}")
        else:
            self.printer(f"بروفايل غير معروف. المتاح: {', '.join(self.profiles.list_profiles())}")

    # ---------- Run / تنفيذ عام ----------

    def cmd_run(self, command: str) -> None:
        if not command:
            self.printer("استخدم: run <أمر>")
            return
        result = self.engine.run(command)
        self.monitor.record(result)
        if result.stdout:
            self.printer(result.stdout)
        if result.stderr:
            self._last_error = result.stderr
            self._last_error_fingerprint = self.error_db.record_error(command, result.stderr)
            self.event_bus.publish(Events.ERROR_OCCURRED, command=command, error=result.stderr)
            self.printer(result.stderr)
        if result.was_blocked:
            self.event_bus.publish(Events.COMMAND_BLOCKED, command=command, reason=result.block_reason)
            self.printer(f"⛔ {result.block_reason}")

    # ---------- شرح / تشخيص / إصلاح ----------

    def cmd_explain(self, command: str) -> None:
        if not command:
            self.printer("استخدم: exp <أمر>")
            return
        engine_obj = self.windows_engine if self.os_name == "Windows" else self.linux_engine
        self.printer(engine_obj.explain_command(command))

    def cmd_fix(self, _: str) -> None:
        if not self._last_error:
            self.printer("لا يوجد خطأ سابق لإصلاحه.")
            return

        known_solution = self.error_db.best_known_solution(self._last_error)
        if known_solution:
            self.printer(f"💡 حل معروف من محاولات سابقة:\n{known_solution}")
            return

        if self.os_name == "Windows":
            fix = self.windows_engine.diagnose_and_fix(self._last_error)
        else:
            fix = self.linux_engine.diagnose_and_fix(self._last_error)

        self.printer(fix)
        if self._last_error_fingerprint:
            self.error_db.record_solution(self._last_error_fingerprint, fix, worked=True)
            self.event_bus.publish(Events.ERROR_FIXED, command="", fix=fix)

    def cmd_diagnose(self, _: str) -> None:
        if self.os_name == "Windows":
            result = self.windows_engine.system_info()
        else:
            result = self.linux_engine.diagnose_system()
        self.printer(result.stdout or result.stderr)

    # ---------- كود ----------

    def cmd_code(self, description: str) -> None:
        if not description:
            self.printer("استخدم: code <وصف الكود المطلوب>")
            return
        self.printer(self.code.write_code(description))

    def cmd_edit(self, args: str) -> None:
        parts = args.split(" ", 1)
        if len(parts) < 2:
            self.printer("استخدم: edit <مسار_الملف> <تعليمات التعديل>")
            return
        file_path, instruction = parts

        snapshot_id = self.snapshots.snapshot_before_edit(file_path, reason=f"قبل: {instruction[:50]}")
        if snapshot_id:
            self.printer(f"💾 نسخة احتياطية ({snapshot_id}) — 'undo {file_path}' للتراجع.")

        self.context_manager.track_open_file(file_path)
        self.printer(self.code.edit_file(file_path, instruction))
        self.event_bus.publish(Events.FILE_EDITED, path=file_path, snapshot_id=snapshot_id or "")

    def cmd_debug(self, code_or_error: str) -> None:
        if not code_or_error:
            self.printer("استخدم: dbg <كود أو رسالة خطأ>")
            return
        self.printer(self.code.debug_code(code_or_error))

    def cmd_review(self, code_text: str) -> None:
        if not code_text:
            self.printer("استخدم: rev <كود>")
            return
        self.printer(self.code.review_code(code_text))

    def cmd_analyze(self, path: str) -> None:
        self.printer(self.analyzer.full_report(path or "."))

    def cmd_make_project(self, name: str) -> None:
        if not name:
            self.printer("استخدم: mk <اسم المشروع>")
            return
        import os
        os.makedirs(name, exist_ok=True)
        self.memory.remember_project(name, os.path.abspath(name))
        self.printer(f"تم إنشاء مشروع جديد: {name}")

    # ---------- Git ----------

    def cmd_git(self, args: str) -> None:
        if not args:
            result = self.git.status()
            self.printer(result.stdout or result.stderr)
            return
        parts = shlex.split(args)
        action = parts[0]

        if action == "clone" and len(parts) >= 2:
            result = self.git.clone(parts[1], parts[2] if len(parts) > 2 else None)
        elif action == "commit" and len(parts) >= 2:
            message = " ".join(parts[1:])
            results = self.git.commit(message)
            for r in results:
                self.printer(r.stdout or r.stderr)
            return
        elif action == "push":
            findings = self.secrets_scanner.scan_directory(".")
            if findings:
                self.printer(f"🚨 تحذير: {len(findings)} سر محتمل مكشوف قبل الـ push!")
                self.printer("استخدم 'secrets' لعرض التفاصيل.")
                confirm = input("المتابعة رغم ذلك؟ [y/N] ").strip().lower()
                if confirm not in ("y", "yes"):
                    self.printer("تم إلغاء الـ push.")
                    return
            force = "--force" in parts
            result = self.git.push(force=force)
        elif action == "pull":
            result = self.git.pull()
        elif action == "branch" and len(parts) >= 2:
            result = self.git.create_branch(parts[1])
        elif action == "checkout" and len(parts) >= 2:
            result = self.git.switch_branch(parts[1])
        elif action == "merge" and len(parts) >= 2:
            result = self.git.merge(parts[1])
        elif action == "log":
            result = self.git.log()
        elif action == "diff":
            result = self.git.diff()
        else:
            self.printer("استخدم: git [clone|commit|push|pull|branch|checkout|merge|log|diff] ...")
            return

        self.printer(result.stdout or result.stderr)

    # ---------- Docker ----------

    def cmd_docker(self, args: str) -> None:
        if not args:
            result = self.docker.list_containers()
            self.printer(result.stdout or result.stderr)
            return
        parts = shlex.split(args)
        action = parts[0]

        if action == "images":
            result = self.docker.list_images()
        elif action == "ps":
            result = self.docker.list_containers()
        elif action == "build" and len(parts) >= 2:
            result = self.docker.build_image(parts[1])
        elif action == "run" and len(parts) >= 2:
            result = self.docker.run_container(parts[1])
        elif action == "stop" and len(parts) >= 2:
            result = self.docker.stop_container(parts[1])
        elif action == "logs" and len(parts) >= 2:
            result = self.docker.logs(parts[1])
        elif action == "exec" and len(parts) >= 3:
            result = self.docker.exec_in_container(parts[1], " ".join(parts[2:]))
        elif action == "compose-up":
            result = self.docker.compose_up()
        elif action == "compose-down":
            result = self.docker.compose_down()
        else:
            self.printer("استخدم: docker [images|ps|build|run|stop|logs|exec|compose-up|compose-down] ...")
            return

        self.printer(result.stdout or result.stderr)

    # ---------- SSH ----------

    def cmd_ssh(self, args: str) -> None:
        parts = shlex.split(args)
        if len(parts) < 2:
            self.printer("استخدم: ssh <host> <command> — أو ssh test <host>")
            return

        host = parts[0]
        target = SSHTarget(host=host)

        if parts[1] == "test":
            result = self.ssh.connect_test(target)
        else:
            command = " ".join(parts[1:])
            result = self.ssh.run_remote_command(target, command)

        self.printer(result.stdout or result.stderr)

    # ---------- Package Manager ----------

    def cmd_pkg(self, args: str) -> None:
        parts = shlex.split(args)
        if len(parts) < 2:
            self.printer("استخدم: pkg install <package> | pkg remove <package> | pkg update | pkg upgrade")
            return

        action, package = parts[0], parts[1] if len(parts) > 1 else ""
        if action == "install":
            result = self.pkg.install(package)
        elif action == "remove":
            result = self.pkg.remove(package)
        elif action == "update":
            result = self.pkg.update_index()
        elif action == "upgrade":
            result = self.pkg.upgrade_all()
        else:
            self.printer("أمر غير معروف. استخدم install/remove/update/upgrade")
            return

        self.printer(result.stdout or result.stderr)

    # ---------- Network ----------

    def cmd_net(self, args: str) -> None:
        parts = shlex.split(args)
        if not parts:
            result = self.net.my_ip()
            self.printer(result.stdout or result.stderr)
            return

        action = parts[0]
        if action == "ping" and len(parts) >= 2:
            result = self.net.ping(parts[1])
        elif action == "trace" and len(parts) >= 2:
            result = self.net.traceroute(parts[1])
        elif action == "dns" and len(parts) >= 2:
            result = self.net.dns_lookup(parts[1])
        elif action == "conns":
            result = self.net.open_connections()
        else:
            self.printer("استخدم: net [ping|trace|dns|conns] <host>")
            return

        self.printer(result.stdout or result.stderr)

    def cmd_scan(self, host: str) -> None:
        if not host:
            self.printer("استخدم: scan <host>")
            return
        self.printer(f"جاري فحص {host}...")
        results = self.net.scan_ports(host)
        open_ports = [str(p) for p, is_open in results.items() if is_open]
        self.printer(f"بورتات مفتوحة: {', '.join(open_ports)}" if open_ports else "لا توجد بورتات مفتوحة.")

    # ---------- Dashboard ----------

    def cmd_dashboard(self, _: str) -> None:
        self.printer(self.dashboard.render())

    # ---------- Providers ----------

    def cmd_model(self, model_name: str) -> None:
        if not model_name:
            self.printer(f"الموديل الحالي: {self.config.get('model')}")
            return
        old_model = self.config.get("model")
        self.providers.switch_model(model_name)
        self.event_bus.publish(Events.MODEL_CHANGED, old=old_model, new=model_name)
        self.printer(f"تم تغيير الموديل إلى: {model_name}")

    def cmd_provider(self, provider_name: str) -> None:
        if not provider_name:
            self.printer(f"الـ Provider الحالي: {self.config.get('provider')}")
            return
        old_provider = self.config.get("provider")
        ok = self.providers.switch_provider(provider_name)
        if ok:
            self.event_bus.publish(Events.PROVIDER_CHANGED, old=old_provider, new=provider_name)
        self.printer("تم التبديل بنجاح." if ok else "Provider غير مدعوم.")

    def cmd_api(self, args: str) -> None:
        parts = args.split()
        if not parts:
            providers_list = self.keys.list_providers()
            self.printer(str(providers_list) if providers_list else "لا توجد مفاتيح مضبوطة بعد.")
            return

        action = parts[0]
        if action == "add" and len(parts) >= 3:
            self.keys.add_key(parts[1], parts[2])
            self.printer(f"تم حفظ مفتاح {parts[1]}.")
        elif action == "remove" and len(parts) >= 2:
            ok = self.keys.remove_key(parts[1])
            self.printer("تم الحذف." if ok else "لم يتم العثور على المفتاح.")
        elif action == "test":
            ok = self.providers.test_current()
            self.printer("✅ الاتصال يعمل." if ok else "❌ فشل الاتصال.")
        else:
            self.printer("استخدم: api add <provider> <key> | api remove <provider> | api test")

    def cmd_config_legacy(self, args: str) -> None:
        """الأمر القديم cfg (طبقة global فقط، للتوافق الرجعي)."""
        if not args:
            self.printer(str(self.config.all()))
            return
        parts = args.split(" ", 1)
        if len(parts) == 2:
            key, value = parts
            self.config.set(key, value)
            self.printer(f"تم تعديل {key} = {value}")
        else:
            self.printer(str(self.config.get(parts[0])))

    def cmd_theme(self, theme_name: str) -> None:
        if not theme_name:
            self.printer(f"الثيم الحالي: {self.config.get('theme')} — المتاح: {', '.join(self.theme.list_themes())}")
            return
        ok = self.theme.set_theme(theme_name)
        if ok:
            self.config.set("theme", theme_name)
            self.printer(f"تم تغيير الثيم إلى: {theme_name}")
        else:
            self.printer(f"ثيم غير معروف. المتاح: {', '.join(self.theme.list_themes())}")

    # ---------- Plugins + Marketplace ----------

    def cmd_plugins(self, args: str) -> None:
        parts = args.split()
        if not parts:
            available = self.plugins.discover()
            loaded = self.plugins.list_loaded()
            self.printer(f"المحلية المتاحة: {available}\nالمُحمّلة: {loaded}")
            return

        action = parts[0]
        if action == "load" and len(parts) >= 2:
            plugin = self.plugins.load(parts[1])
            if plugin:
                self.event_bus.publish(Events.PLUGIN_LOADED, name=parts[1])
                # دمج أوامر الإضافة في جدول التوزيع الحالي
                self._dispatch_table.update(plugin.register_commands())
            self.printer(f"تم تحميل {parts[1]}." if plugin else "فشل التحميل.")
        elif action == "unload" and len(parts) >= 2:
            ok = self.plugins.unload(parts[1])
            if ok:
                self.event_bus.publish(Events.PLUGIN_UNLOADED, name=parts[1])
            self.printer("تم الإيقاف." if ok else "لم يتم العثور على الإضافة.")
        elif action == "install" and len(parts) >= 2:
            self.printer(self.marketplace.install(parts[1]))
        elif action == "search" and len(parts) >= 2:
            self.printer(self.marketplace.render_search_results(parts[1]))
        elif action == "update" and len(parts) >= 2:
            self.printer(self.marketplace.update(parts[1]))
        elif action == "publish" and len(parts) >= 2:
            self.printer(self.marketplace.publish_instructions(parts[1]))
        else:
            self.printer("استخدم: plug [load|unload|install|search|update|publish] <اسم>")

    # ---------- History / Session ----------

    def cmd_history(self, args: str) -> None:
        if args:
            results = self.history.search(args)
            self.printer("\n".join(results) if results else "لا توجد نتائج.")
            return
        recent = self.history.last(15)
        self.printer("\n".join(recent) if recent else "لا يوجد سجل بعد.")

    def cmd_session(self, args: str) -> None:
        parts = args.split()
        if not parts:
            self.printer(self.session.summary())
            self.printer(self.monitor.summary())
            return

        action = parts[0]
        if action == "list":
            self.printer(SessionManager.render_list())
        elif action == "switch" and len(parts) >= 2:
            self.printer(f"لتبديل الجلسة، أعد تشغيل cai مع: CAI_RESUME_SESSION={parts[1]} cai")
        elif action == "resume" and len(parts) >= 2:
            data = SessionManager.load_session(parts[1])
            if data:
                self.printer(f"جلسة {parts[1]}: {len(data['commands'])} أمر، بدأت {data['started_at']}")
            else:
                self.printer("جلسة غير موجودة.")
        elif action == "archive" and len(parts) >= 2:
            ok = SessionManager.archive(parts[1])
            self.printer("تمت الأرشفة." if ok else "جلسة غير موجودة.")
        else:
            self.printer("استخدم: session [list|switch|resume|archive] <id>")

    def cmd_memory(self, _: str) -> None:
        messages = self.memory.recent_messages(10)
        if not messages:
            self.printer("لا توجد محادثات محفوظة بعد.")
            return
        for m in messages:
            self.printer(f"[{m['role']}] {m['content'][:100]}")

    def cmd_clear(self, _: str) -> None:
        import os
        os.system("cls" if os.name == "nt" else "clear")

    def cmd_exit(self, _: str) -> None:
        self.session.end_session()
        self._should_exit = True

    def cmd_chat(self, user_input: str) -> None:
        context = self.auto_context.build_context_summary()
        contextual_prompt = f"سياق بيئة العمل الحالية:\n{context}\n\nسؤال/طلب المستخدم:\n{user_input}"
        response = self.providers.chat([ChatMessage(role="user", content=contextual_prompt)])
        if response.ok:
            self.printer(response.content)
            self.memory.add_message("assistant", response.content)
        else:
            self._last_error = response.error
            self.printer(f"❌ خطأ: {response.error}")

    # ---------- Multi-Agent Team ----------

    def cmd_team(self, task: str) -> None:
        if not task:
            self.printer("استخدم: team <وصف مهمة برمجية متكاملة>")
            return

        self.printer("🧠 الفريق شغال: Architect → Coder → Reviewer → Fixer ...\n")

        def on_update(msg):
            self.printer(f"── {msg.agent} ──\n{msg.content}\n")

        result = self.multi_agent.run(task, on_agent_update=on_update)
        self.printer("\n✅ الكود النهائي جاهز.")
        save = input("هل تريد حفظه في ملف؟ (اكتب المسار أو اتركه فارغًا للتخطي): ").strip()
        if save:
            with open(save, "w", encoding="utf-8") as f:
                f.write(result.final_code)
            self.printer(f"تم الحفظ في: {save}")

    # ---------- Web Search ----------

    def cmd_search(self, query: str) -> None:
        if not query:
            self.printer("استخدم: search <سؤال أو موضوع>")
            return
        self.printer("🔎 جاري البحث...")
        self.printer(self.web_search.search_and_summarize(query))

    # ---------- Workflow Templates (الجاهزة) ----------

    def cmd_template(self, args: str) -> None:
        parts = args.split()
        if not parts:
            self.printer(self.templates.describe_all())
            return

        key = parts[0]
        project_name = parts[1] if len(parts) > 1 else "my_project"
        template = self.templates.get(key, project_name)

        if not template:
            self.printer(f"قالب غير معروف: {key}\n\n{self.templates.describe_all()}")
            return

        self.printer(f"القالب: {template.title}\n{template.description}\n")
        for i, step in enumerate(template.steps, 1):
            cmd_part = f"  →  {step.command}" if step.command else "  (بدون أمر تنفيذي)"
            self.printer(f"{i}. {step.description}{cmd_part}")

        confirm = input("\nتنفيذ القالب كاملاً؟ [Y/n] ").strip().lower()
        if confirm not in ("", "y", "yes"):
            self.printer("تم الإلغاء.")
            return

        for step in template.steps:
            if step.command:
                self.printer(f"\n▶ {step.description}")
                result = self.engine.run(step.command)
                self.printer(result.stdout or result.stderr)

    # ---------- Script Generator ----------

    def cmd_script(self, args: str) -> None:
        if not args:
            self.printer("استخدم: script <وصف السكريبت>")
            return

        description = args
        language = None
        for lang_key in ("bash", "python", "powershell"):
            if description.lower().startswith(f"{lang_key}:"):
                language = lang_key
                description = description.split(":", 1)[1].strip()
                break

        self.printer("⚙️ جاري توليد السكريبت...")
        code = self.script_gen.generate(description, language=language)
        self.printer(code)

        save_path = input("\nاحفظ السكريبت في مسار (اتركه فارغًا للتخطي): ").strip()
        if save_path:
            self.printer(self.script_gen.generate_and_save(description, save_path, language=language))

    # ---------- Auto Context ----------

    def cmd_context(self, root: str) -> None:
        self.printer(self.context_manager.build_prompt_context())

    # ---------- Voice ----------

    def cmd_voice(self, _: str) -> None:
        if not self.voice.is_available():
            self.printer(self.voice.installation_hint())
            return
        self.printer("🎙️ جاري الاستماع... تكلم الآن.")
        text = self.voice.listen_once()
        if not text:
            self.printer("لم يتم التعرف على أي كلام.")
            return
        self.printer(f"تم فهم: {text}")
        self.handle(text)

    # ---------- Cost Tracker ----------

    def cmd_cost(self, _: str) -> None:
        self.printer(self.cost_tracker.render_report())

    # ---------- Snapshot / Undo ----------

    def cmd_snapshot(self, args: str) -> None:
        if not args:
            snapshots = self.snapshots.list_snapshots(limit=15)
            if not snapshots:
                self.printer("لا توجد نسخ احتياطية محفوظة بعد.")
                return
            for s in snapshots:
                self.printer(f"[{s.id}] {s.original_path} — {s.reason}")
            return

        parts = args.split()
        if parts[0] == "restore" and len(parts) >= 2:
            self.printer(self.snapshots.restore(parts[1]))
        else:
            self.printer("استخدم: snapshot — أو: snapshot restore <id>")

    def cmd_undo(self, file_path: str) -> None:
        if not file_path:
            self.printer("استخدم: undo <مسار_الملف>")
            return
        result = self.snapshots.undo_last(file_path)
        self.printer(result)
        self.event_bus.publish(Events.FILE_RESTORED, path=file_path, snapshot_id="")

    # ---------- Secrets Scanner ----------

    def cmd_secrets(self, path: str) -> None:
        self.printer("🔍 جاري فحص المشروع بحثًا عن مفاتيح مكشوفة...")
        self.printer(self.secrets_scanner.render_report(path or "."))

    # ---------- Pre-Deploy Health Check ----------

    def cmd_predeploy(self, path: str) -> None:
        self.printer("🏥 جاري فحص جاهزية المشروع للنشر...")
        self.printer(self.health_check.render_report(path or "."))

    # ---------- Auto Documentation ----------

    def cmd_docgen(self, args: str) -> None:
        parts = args.split()
        target = parts[0] if parts else "."

        self.printer("📝 جاري توليد التوثيق...")
        docs = self.doc_generator.generate_file_docs(target) if Path(target).is_file() \
            else self.doc_generator.generate_project_docs(target)

        self.printer(docs)
        save_path = input("\nاحفظ في ملف (اتركه فارغًا للتخطي): ").strip()
        if save_path:
            self.printer(self.doc_generator.save_docs(docs, save_path))

    # ---------- Alias System ----------

    def cmd_alias(self, args: str) -> None:
        if not args:
            self.printer(self.aliases.render_list())
            return

        parts = args.split(" ", 1)
        action = parts[0]

        if action == "add" and len(parts) >= 2 and "=" in parts[1]:
            name, expansion = parts[1].split("=", 1)
            self.printer(self.aliases.add(name, expansion))
        elif action == "remove" and len(parts) >= 2:
            self.printer(self.aliases.remove(parts[1]))
        elif action == "list":
            self.printer(self.aliases.render_list())
        else:
            self.printer("استخدم: alias add <اسم> = <أمر> | alias remove <اسم> | alias list")

    # ---------- Background Jobs ----------

    def cmd_jobs(self, _: str) -> None:
        self.printer(self.jobs.render_list())

    def cmd_bg(self, command: str) -> None:
        if not command:
            self.printer("استخدم: bg <أمر> — يشغّله في الخلفية فورًا")
            return
        job = self.jobs.start(command)
        self.event_bus.publish(Events.JOB_STARTED, job_id=job.id, command=command)
        self.printer(f"🚀 بدأت Job #{job.id} في الخلفية: {command}")

    def cmd_fg(self, job_id_str: str) -> None:
        if not job_id_str or not job_id_str.isdigit():
            self.printer("استخدم: fg <رقم الـ job>")
            return
        output = self.jobs.bring_to_foreground(int(job_id_str))
        self.printer(output)

    def cmd_kill(self, job_id_str: str) -> None:
        if not job_id_str or not job_id_str.isdigit():
            self.printer("استخدم: kill <رقم الـ job>")
            return
        job_id = int(job_id_str)
        self.printer(self.jobs.kill(job_id))
        self.event_bus.publish(Events.JOB_FINISHED, job_id=job_id, success=False)

    # ---------- Workflow ----------

    def cmd_workflow(self, args: str) -> None:
        parts = args.split(" ", 1)
        if not parts or not parts[0]:
            names = self.workflows.list_workflows()
            self.printer(f"سير العمل المحفوظة: {names}" if names else "لا يوجد سير عمل محفوظ.")
            self.printer("استخدم: workflow [create|add-step|run|show|export|import] ...")
            return

        action = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

        if action == "create":
            name_parts = rest.split(" ", 1)
            name = name_parts[0]
            description = name_parts[1] if len(name_parts) > 1 else ""
            self.workflows.create(name, description)
            self.printer(f"تم إنشاء سير العمل: {name}")

        elif action == "add-step":
            step_parts = rest.split(" ", 2)
            if len(step_parts) < 3:
                self.printer("استخدم: workflow add-step <اسم> <shell|ai|tool> <القيمة>")
                return
            name, kind, value = step_parts
            self.printer(self.workflows.add_step(name, kind, value))

        elif action == "run" and rest:
            self.event_bus.publish(Events.WORKFLOW_STARTED, workflow_name=rest)

            def shell_runner(cmd):
                result = self.engine.run(cmd)
                return result.stdout or result.stderr

            def ai_runner(prompt):
                response = self.providers.chat([ChatMessage(role="user", content=prompt)])
                return response.content if response.ok else f"خطأ: {response.error}"

            def tool_runner(tool_name, tool_args):
                result = self.tool_registry.call(tool_name, tool_args)
                return result.to_message_content()

            def on_step(i, step, output):
                self.printer(f"[{i}] {step.kind}: {step.value}\n  → {output[:200]}")

            results = self.workflows.run(rest, shell_runner, ai_runner, tool_runner, on_step=on_step)
            self.event_bus.publish(Events.WORKFLOW_FINISHED, workflow_name=rest, success=True)
            self.printer(f"\n✅ اكتمل سير العمل ({len(results)} خطوة).")

        elif action == "show" and rest:
            self.printer(self.workflows.render_details(rest))

        elif action == "export" and rest:
            export_parts = rest.split()
            if len(export_parts) < 2:
                self.printer("استخدم: workflow export <اسم> <مسار الحفظ>")
                return
            self.printer(self.workflows.export(export_parts[0], export_parts[1]))

        elif action == "import" and rest:
            self.printer(self.workflows.import_from(rest))

        else:
            self.printer("استخدم: workflow [create|add-step|run|show|export|import] ...")

    # ---------- Macro ----------

    def cmd_macro(self, args: str) -> None:
        parts = args.split(" ", 1)
        if not parts or not parts[0]:
            names = self.macros.list_macros()
            self.printer(f"الماكرو المحفوظ: {names}" if names else "لا يوجد ماكرو محفوظ.")
            return

        action = parts[0]
        rest = parts[1] if len(parts) > 1 else ""

        if action == "record":
            self.printer(self.macros.start())
        elif action == "stop":
            commands = self.macros.stop()
            self.printer(f"تم إيقاف التسجيل ({len(commands)} أمر). استخدم: macro save <اسم>")
        elif action == "save" and rest:
            self.printer(self.macros.save(rest))
        elif action == "run" and rest:
            self.printer(self.macros.run(rest, executor=self.handle))
        elif action == "show" and rest:
            self.printer(self.macros.render_details(rest))
        else:
            self.printer("استخدم: macro [record|stop|save|run|show] <اسم>")

    # ---------- Layered Config ----------

    def cmd_config(self, args: str) -> None:
        if not args:
            self.printer(self.layered_config.render_layers())
            return

        parts = args.split()
        if parts[0] == "get" and len(parts) >= 2:
            self.printer(self.layered_config.explain(parts[1]))
        elif parts[0] == "set" and len(parts) >= 3:
            layer = parts[3] if len(parts) >= 4 else "session"
            self.printer(self.layered_config.set(parts[1], parts[2], layer=layer))
        else:
            self.printer("استخدم: config get <key> | config set <key> <value> [layer]")

    # ---------- Error Database ----------

    def cmd_errors(self, _: str) -> None:
        self.printer(self.error_db.render_report())

    # ---------- Offline Mode ----------

    def cmd_offline(self, _: str) -> None:
        online = self.offline_mode.is_internet_available()
        self.printer("🌐 متصل بالإنترنت." if online else "🔌 غير متصل بالإنترنت.")
        if not online:
            self.printer("استخدم: provider ollama للتحويل لنموذج محلي.")

    # ---------- Telemetry ----------

    def cmd_telemetry(self, args: str) -> None:
        if args in ("on", "enable"):
            self.printer(self.telemetry.set_enabled(True))
            self.config.set("telemetry_enabled", True)
        elif args in ("off", "disable"):
            self.printer(self.telemetry.set_enabled(False))
            self.config.set("telemetry_enabled", False)
        elif args == "clear":
            self.printer(self.telemetry.clear_data())
        else:
            self.printer(self.telemetry.export_local_report())

    # ---------- Doctor (فحص شامل لصحة النظام) ----------

    def cmd_doctor(self, _: str) -> None:
        lines = ["── cai Doctor ─────────────────"]
        status = self.providers.status()
        lines.append(f"AI Provider: {'✅' if status['configured'] else '❌'} {status['provider']}")

        online = self.offline_mode.is_internet_available()
        lines.append(f"اتصال الإنترنت: {'✅' if online else '❌'}")

        snap = self.dashboard.snapshot()
        if snap.available:
            lines.append(f"موارد النظام: CPU {snap.cpu_percent}% | RAM {snap.ram_percent}%")

        secrets_count = len(self.secrets_scanner.scan_directory("."))
        lines.append(f"أسرار مكشوفة في المجلد الحالي: {'❌ ' + str(secrets_count) if secrets_count else '✅ لا يوجد'}")

        lines.append(f"عدد الأدوات المسجّلة (Tool Registry): {len(self.tool_registry.list_tools())}")
        lines.append(f"عدد الإضافات المحمّلة: {len(self.plugins.list_loaded())}")

        self.printer("\n".join(lines))

    # ---------- Whoami ----------

    def cmd_whoami(self, _: str) -> None:
        self.printer(
            f"Profile: {self.profiles.active.display_name}\n"
            f"Mode: {self.config.get('mode')}\n"
            f"Provider: {self.config.get('provider')} / {self.config.get('model')}\n"
            f"Session: {self.session.session_id}\n"
            f"OS: {self.os_name}"
        )

    # ---------- Pixel CommandAI: الحساب والاشتراك ----------

    def cmd_signup(self, _: str) -> None:
        import getpass
        import json
        import urllib.request

        self.printer("إنشاء حساب Pixel CommandAI جديد")
        full_name = input("الاسم بالكامل: ").strip()
        email = input("البريد الإلكتروني: ").strip()
        password = getpass.getpass("كلمة المرور: ")
        phone = input("رقم الهاتف [اختياري]: ").strip() or None
        purpose = input("الاستخدام الأساسي (developer/devops/security/student/other) [اختياري]: ").strip() or None

        # تحديد الدولة تلقائيًا عبر IP — بدون أي إذن مطلوب من المستخدم.
        country = None
        try:
            req = urllib.request.Request(f"{PIXEL_SUPABASE_URL}/functions/v1/detect-country")
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                country = data.get("country_code")
        except Exception:
            pass  # لو فشل التحديد التلقائي، هيتحدد لاحقًا كسعر افتراضي (US)

        if country:
            confirm = input(f"دولتك المكتشفة: {country} — صح؟ (Enter للتأكيد، أو اكتب رمز تاني): ").strip().upper()
            if confirm:
                country = confirm
        else:
            country = input("رمز الدولة (مثال: EG, US, SA) [اختياري]: ").strip().upper() or None

        try:
            result = self.pixel_auth.sign_up(
                email, password,
                country_code=country, full_name=full_name or None, phone=phone, usage_purpose=purpose,
            )
            if result.get("access_token"):
                self.printer("تم إنشاء الحساب وتسجيل الدخول بنجاح. خطتك الحالية: Free")
            else:
                self.printer("تم إنشاء الحساب! افتح بريدك الإلكتروني واضغط على رابط التأكيد، وبعدين استخدم `login`.")
        except AuthError as e:
            self.printer(f"فشل إنشاء الحساب: {e}")

    def cmd_login(self, _: str) -> None:
        import getpass
        email = input("البريد الإلكتروني: ").strip()
        password = getpass.getpass("كلمة المرور: ")
        try:
            self.pixel_auth.sign_in(email, password)
            self.printer("تم تسجيل الدخول بنجاح.")
        except AuthError as e:
            self.printer(f"فشل تسجيل الدخول: {e}")

    def cmd_logout(self, _: str) -> None:
        self.pixel_auth.sign_out()
        self.printer("تم تسجيل الخروج.")

    def cmd_account(self, _: str) -> None:
        if not self.pixel_auth.is_logged_in():
            self.printer("لم يتم تسجيل الدخول. استخدم: login")
            return
        user = self.pixel_auth.current_user() or {}
        email = user.get("email", "غير معروف")
        self.printer(f"الحساب: {email}")
        self.printer("لعرض تفاصيل الخطة والاستخدام الحالي، شغّل: status")

    def cmd_upgrade(self, args: str) -> None:
        import json
        import urllib.request
        import urllib.error

        plan_id = args.strip().lower()
        if plan_id not in ("basic", "pro"):
            self.printer("الاستخدام: upgrade [basic|pro]")
            return
        if not self.pixel_auth.is_logged_in():
            self.printer("لازم تسجل الدخول الأول: login")
            return

        try:
            token = self.pixel_auth.get_access_token()
        except AuthError as e:
            self.printer(f"خطأ في الجلسة: {e}")
            return

        # ملاحظة: الدفع بالعملات الرقمية (NOWPayments / create-invoice) متوقف
        # مؤقتًا. الترقية حاليًا بالبطاقة عبر Lemon Squeezy (create-checkout).
        url = f"{PIXEL_SUPABASE_URL}/functions/v1/create-checkout"
        body = json.dumps({"plan_id": plan_id}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8", errors="ignore")
            self.printer(f"فشل إنشاء رابط الدفع: {raw}")
            return

        checkout_url = data.get("checkout_url")
        if not checkout_url:
            self.printer(f"استجابة غير متوقعة: {data}")
            return
        self.printer(f"افتح الرابط ده عشان تكمل الدفع بالبطاقة:\n{checkout_url}")
        self.printer("خطتك هتترقّي تلقائيًا بمجرد تأكيد الدفع (عادة خلال دقائق).")

    # ---------- Metrics ----------

    def cmd_metrics(self, _: str) -> None:
        self.printer(self.monitor.summary())
        self.printer("")
        self.printer(self.cost_tracker.render_report())

    # ---------- Termux / Android ----------

    def cmd_termux(self, args: str) -> None:
        if not self.platform_info.is_termux:
            self.printer("cai مش شغال داخل Termux حاليًا (النظام المكتشف: " + self.platform_info.os_name + ").")
            return

        if not args:
            self.printer(self.platform_info.summary())
            return

        if args == "api":
            self.printer(self.termux_api.render_device_summary())
        else:
            self.printer("استخدم: termux — أو: termux api")

    def cmd_storage(self, args: str) -> None:
        if not self.platform_info.is_termux:
            self.printer("أمر storage مخصص لبيئة Termux فقط.")
            return

        if not args:
            self.printer(self.storage.render_summary())
            return

        shortcut_path = self.storage.resolve_shortcut(args)
        if shortcut_path:
            self.printer(str(shortcut_path))
        else:
            self.printer(f"مجلد غير معروف أو غير متاح: {args}\n{self.storage.request_setup_instructions()}")

    def cmd_ollama(self, args: str) -> None:
        parts = args.split(" ", 1)
        action = parts[0] if parts else ""

        if not action or action == "status":
            self.printer(self.providers.ollama_connector.render_status())
        elif action == "connect" and len(parts) > 1:
            self.printer(self.providers.ollama_connector.set_remote_url(parts[1].strip()))
        else:
            self.printer("استخدم: ollama status — أو: ollama connect <http://IP:11434>")

    def cmd_phone(self, args: str) -> None:
        """أوامر سريعة لأدوات Termux:API الشائعة (بدون الحاجة لتذكر أسماء أوامر termux-* الفعلية)."""
        if not self.termux_api.is_available():
            self.printer(self.platform_info.termux_api_setup_hint())
            return

        parts = args.split(" ", 1)
        action = parts[0] if parts else ""
        value = parts[1] if len(parts) > 1 else ""

        if action == "battery":
            status = self.termux_api.battery_status()
            self.printer(str(status) if status else "تعذّر جلب حالة البطارية.")
        elif action == "notify" and value:
            ok = self.termux_api.show_notification("cai", value)
            self.printer("✅ تم إرسال الإشعار." if ok else "❌ فشل إرسال الإشعار.")
        elif action == "vibrate":
            ok = self.termux_api.vibrate()
            self.printer("✅ تم الاهتزاز." if ok else "❌ فشل.")
        elif action == "toast" and value:
            ok = self.termux_api.toast(value)
            self.printer("✅ تم العرض." if ok else "❌ فشل.")
        elif action == "clipboard":
            text = self.termux_api.clipboard_get()
            self.printer(text or "الحافظة فارغة أو تعذّر الوصول لها.")
        elif action == "speak" and value:
            ok = self.termux_api.speak(value)
            self.printer("✅ تم النطق." if ok else "❌ فشل.")
        elif action == "location":
            location = self.termux_api.get_location()
            self.printer(str(location) if location else "تعذّر جلب الموقع (تأكد من منح إذن الموقع).")
        else:
            self.printer(
                "استخدم: phone [battery|notify <رسالة>|vibrate|toast <رسالة>|clipboard|speak <نص>|location]"
            )

    # ---------- Config Sync ----------

    def cmd_sync(self, args: str) -> None:
        parts = args.split(" ", 1)
        if not parts or not parts[0]:
            self.printer("استخدم: sync export <مسار الملف> — أو: sync import <مسار الملف>")
            return

        action = parts[0]
        path = parts[1].strip() if len(parts) > 1 else ""

        if action == "export":
            path = path or "cai_config_bundle.json"
            self.printer(self.config_sync.export_bundle(path))
        elif action == "import" and path:
            self.printer(self.config_sync.import_bundle(path))
        else:
            self.printer("استخدم: sync export <مسار الملف> — أو: sync import <مسار الملف>")
