"""
Dependency Injection Container
---------------------------------
حاوية مركزية لكل خدمات cai (Logger, Config, Memory, Provider, EventBus...).
بدل ما كل Module ينشئ اعتمادياته بنفسه (زي ما كان الحال في v1)، أي Module
دلوقتي بيطلب اعتمادياته من الـ Container، وده بيدي:

- نقطة واحدة للتحكم في دورة حياة كل خدمة (Singleton أو Factory).
- سهولة استبدال أي اعتمادية وقت الاختبار (Testing) بنسخة وهمية.
- تقليل الاعتماد المباشر بين الملفات (Coupling).

طريقة الاستخدام:
    container = Container()
    container.register_singleton("config", lambda c: ConfigManager())
    container.register_singleton("logger", lambda c: get_logger())
    config = container.resolve("config")
"""

from typing import Any, Callable, Dict, Optional


class ServiceNotRegisteredError(Exception):
    pass


class Container:
    def __init__(self):
        self._factories: Dict[str, Callable[["Container"], Any]] = {}
        self._singletons: Dict[str, Any] = {}
        self._singleton_flags: Dict[str, bool] = {}

    def register_singleton(self, name: str, factory: Callable[["Container"], Any]) -> None:
        """يسجل خدمة تُبنى مرة واحدة فقط وتُعاد نفس النسخة في كل resolve."""
        self._factories[name] = factory
        self._singleton_flags[name] = True

    def register_factory(self, name: str, factory: Callable[["Container"], Any]) -> None:
        """يسجل خدمة تُبنى من جديد في كل مرة يُطلب فيها resolve."""
        self._factories[name] = factory
        self._singleton_flags[name] = False

    def register_instance(self, name: str, instance: Any) -> None:
        """يسجل نسخة جاهزة مسبقًا مباشرة (مفيد وقت الاختبار)."""
        self._singletons[name] = instance
        self._singleton_flags[name] = True
        self._factories[name] = lambda c: instance

    def resolve(self, name: str) -> Any:
        if name in self._singletons:
            return self._singletons[name]

        factory = self._factories.get(name)
        if factory is None:
            raise ServiceNotRegisteredError(f"الخدمة غير مسجّلة في الـ Container: '{name}'")

        instance = factory(self)

        if self._singleton_flags.get(name, False):
            self._singletons[name] = instance

        return instance

    def is_registered(self, name: str) -> bool:
        return name in self._factories or name in self._singletons

    def override(self, name: str, instance: Any) -> None:
        """يستبدل خدمة مسجّلة بنسخة تانية (مفيد جدًا في الاختبارات الوحدوية)."""
        self.register_instance(name, instance)

    def reset(self, name: Optional[str] = None) -> None:
        """يمسح نسخة singleton محفوظة (أو الكل) عشان تتبني من جديد عند الطلب التالي."""
        if name:
            self._singletons.pop(name, None)
        else:
            self._singletons.clear()

    def list_services(self) -> list:
        return sorted(set(self._factories.keys()) | set(self._singletons.keys()))
