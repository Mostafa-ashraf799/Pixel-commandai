"""
Event Bus
---------
نظام أحداث مركزي (Pub/Sub) بيخلي الوحدات المختلفة في cai تتواصل من غير
ما توحدة تعرف تفاصيل التانية مباشرة (Loose Coupling).

بدل ما CommandRouter ينادي مباشرة على Logger.log() و Memory.save() و
Monitor.record() في كل مكان، بينشر حدث واحد زي CommandExecuted، وأي
جزء مهتم (Logger, Monitor, Telemetry, Plugins...) بيسمعه ويتصرف بمفرده.

الأحداث الأساسية المعرّفة في cai (انظر events.py لتعريفاتها الكاملة):
    TaskStarted, TaskFinished, PluginLoaded, ProviderChanged, CommandExecuted,
    ErrorOccurred, SessionStarted, SessionEnded, FileEdited
"""

from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class Event:
    name: str
    payload: Dict[str, Any] = field(default_factory=dict)


EventHandler = Callable[[Event], None]


class EventBus:
    def __init__(self):
        self._subscribers: Dict[str, List[EventHandler]] = defaultdict(list)
        self._history: List[Event] = []
        self._max_history: int = 500

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        """يسجّل دالة تُستدعى تلقائيًا كل ما يُنشر حدث بهذا الاسم."""
        self._subscribers[event_name].append(handler)

    def unsubscribe(self, event_name: str, handler: EventHandler) -> bool:
        handlers = self._subscribers.get(event_name, [])
        if handler in handlers:
            handlers.remove(handler)
            return True
        return False

    def publish(self, event_name: str, **payload) -> Event:
        """
        ينشر حدث لكل المشتركين فيه. أي استثناء في handler واحد لا يوقف باقي
        الـ handlers (عزل الأخطاء) — بيتسجل فقط كـ print تحذيري بسيط.
        """
        event = Event(name=event_name, payload=payload)
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history.pop(0)

        for handler in list(self._subscribers.get(event_name, [])):
            try:
                handler(event)
            except Exception as e:
                print(f"⚠️ خطأ في معالج الحدث '{event_name}': {e}")

        return event

    def subscriber_count(self, event_name: str) -> int:
        return len(self._subscribers.get(event_name, []))

    def recent_events(self, limit: int = 20) -> List[Event]:
        return self._history[-limit:]

    def clear_history(self) -> None:
        self._history.clear()
