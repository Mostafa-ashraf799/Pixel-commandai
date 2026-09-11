"""
Event Subscribers Wiring
---------------------------
يربط الخدمات الأساسية (Logger, Session, Memory) كمستمعين افتراضيين على
الـ EventBus، عشان لما أي جزء من البرنامج ينشر حدث زي CommandExecuted،
يحصل تسجيل تلقائي في اللوج والـ Session بدون ما الناشر (Publisher) يعرف
حاجة عن Logger أو Session أصلاً — وده جوهر فكرة الـ Event-Driven Architecture.
"""

from cai.core.di.container import Container
from cai.core.events.events import Events
from cai.utils.logger import log_command, log_error, log_ai_action


def wire_default_subscribers(container: Container) -> None:
    event_bus = container.resolve("event_bus")
    session = container.resolve("session")
    memory = container.resolve("memory")

    def on_command_executed(event):
        command = event.payload.get("command", "")
        success = event.payload.get("success", True)
        risk = event.payload.get("risk", "safe")
        log_command(command, risk)
        session.record_command(command, success=success)

    def on_error_occurred(event):
        command = event.payload.get("command", "")
        error = event.payload.get("error", "")
        log_error(f"{command} -> {error}")
        memory.log_error(command, error)

    def on_provider_changed(event):
        log_ai_action("ProviderChanged", f"{event.payload.get('old')} -> {event.payload.get('new')}")

    def on_plugin_loaded(event):
        log_ai_action("PluginLoaded", event.payload.get("name", ""))

    def on_task_finished(event):
        status = "نجحت" if event.payload.get("success") else "فشلت"
        log_ai_action("TaskFinished", f"{event.payload.get('task', '')} ({status})")

    def on_secret_detected(event):
        log_error(f"SECRET_DETECTED in {event.payload.get('file', '')}: {event.payload.get('pattern', '')}")

    event_bus.subscribe(Events.COMMAND_EXECUTED, on_command_executed)
    event_bus.subscribe(Events.ERROR_OCCURRED, on_error_occurred)
    event_bus.subscribe(Events.PROVIDER_CHANGED, on_provider_changed)
    event_bus.subscribe(Events.PLUGIN_LOADED, on_plugin_loaded)
    event_bus.subscribe(Events.TASK_FINISHED, on_task_finished)
    event_bus.subscribe(Events.SECRET_DETECTED, on_secret_detected)
