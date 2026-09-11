"""
Shell
-----
حلقة التفاعل الرئيسية (REPL). دلوقتي بتستخدم DI Container لبناء كل
الخدمات بدل التهيئة اليدوية المباشرة، وبتربط EventBus مع Crash Recovery
و Terminal Recorder من بداية التشغيل.
"""

from cai.core.di.bootstrap import build_container
from cai.core.events.subscribers import wire_default_subscribers
from cai.core.events.events import Events
from cai.security.permission_manager import RiskLevel
from cai.commands.command_router import CommandRouter
from cai.ui.banner import render_banner
from cai.core.crash_recovery import CrashRecoveryManager
from cai.core.terminal_recorder import TerminalRecorder


def confirm_dangerous_command(command: str, risk: RiskLevel, explanation: str) -> bool:
    print(f"\n{explanation}")
    print(f"الأمر: {command}")
    if risk == RiskLevel.CRITICAL:
        answer = input('اكتب "yes" بالكامل للتأكيد: ').strip().lower()
        return answer == "yes"
    answer = input("هل تريد المتابعة؟ [y/N] ").strip().lower()
    return answer in ("y", "yes")


class Shell:
    def __init__(self):
        self.container = build_container()

        self.config = self.container.resolve("config")
        self.keys = self.container.resolve("keys")
        self.permissions = self.container.resolve("permissions")
        self.providers = self.container.resolve("providers")
        self.engine = self.container.resolve("engine")
        self.engine.confirm_callback = confirm_dangerous_command  # يحتاج input() تفاعلي، يُضبط هنا
        self.memory = self.container.resolve("memory")
        self.history = self.container.resolve("history")
        self.session = self.container.resolve("session")
        self.cost_tracker = self.container.resolve("cost_tracker")
        self.event_bus = self.container.resolve("event_bus")
        self.logger = self.container.resolve("logger")

        wire_default_subscribers(self.container)

        self.crash_recovery = CrashRecoveryManager()
        self.recorder = TerminalRecorder()

        self.router = CommandRouter(container=self.container, printer=self._printer)

    def _printer(self, text: str) -> None:
        print(text)
        self.recorder.write_output(text)

    def _check_crash_recovery(self) -> None:
        crash_data = self.crash_recovery.check_for_crash()
        if crash_data:
            print(self.crash_recovery.render_recovery_prompt(crash_data))
            print()

    def run(self) -> None:
        self._check_crash_recovery()
        print(render_banner(self.config, self.providers))
        self.event_bus.publish(Events.SESSION_STARTED, session_id=self.session.session_id)

        while not self.router.should_exit:
            try:
                user_input = input("cai > ")
            except (EOFError, KeyboardInterrupt):
                print("\nExiting...")
                break

            self.recorder.write_input(user_input)
            self.crash_recovery.heartbeat(self.session.session_id, last_command=user_input)

            try:
                self.router.handle(user_input)
            except Exception as e:
                self.logger.error(f"Unhandled error: {e}")
                print(f"❌ حدث خطأ غير متوقع: {e}")

        self.event_bus.publish(Events.SESSION_ENDED, session_id=self.session.session_id)
        self.crash_recovery.mark_clean_exit()
        if self.recorder.is_recording:
            self.recorder.stop()


def main():
    Shell().run()


if __name__ == "__main__":
    main()
