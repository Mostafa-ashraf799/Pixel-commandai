"""
Plugin System
-------------
يسمح بتوسيع cai عبر Plugins خارجية: كل Plugin عبارة عن ملف/مجلد بايثون
تحت ~/.cai/plugins/ يحتوي على كلاس يرث من PluginBase.

هذا نظام تحميل ديناميكي بسيط (بدون Marketplace فعلي بعد،
لكن البنية جاهزة لإضافته لاحقًا كطبقة فوق هذا الملف).
"""

import importlib.util
import json
import os
from pathlib import Path
from typing import Callable, Dict, List, Optional


class PluginBase:
    """كل Plugin لازم يرث من الكلاس ده."""

    name: str = "unnamed_plugin"
    description: str = ""
    version: str = "0.1.0"

    def register_commands(self) -> Dict[str, Callable[[str], None]]:
        """يرجع dict من {اسم_الأمر: الدالة} عشان الـ Router يضيفها."""
        return {}

    def on_load(self) -> None:
        pass

    def on_unload(self) -> None:
        pass


class PluginManager:
    def __init__(self, plugins_dir: str = None):
        self.plugins_dir = Path(plugins_dir or os.path.expanduser("~/.cai/plugins"))
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        self.registry_path = self.plugins_dir / "registry.json"
        self.loaded_plugins: Dict[str, PluginBase] = {}

    def _load_registry(self) -> Dict[str, bool]:
        if not self.registry_path.exists():
            return {}
        try:
            with open(self.registry_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_registry(self, registry: Dict[str, bool]) -> None:
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=2)

    def discover(self) -> List[str]:
        """يرجع أسماء ملفات .py الموجودة في مجلد الإضافات (بدون تحميلها)."""
        return [f.stem for f in self.plugins_dir.glob("*.py") if not f.stem.startswith("_")]

    def _import_module(self, plugin_file: Path):
        spec = importlib.util.spec_from_file_location(plugin_file.stem, plugin_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def load(self, plugin_name: str) -> Optional[PluginBase]:
        plugin_file = self.plugins_dir / f"{plugin_name}.py"
        if not plugin_file.exists():
            return None

        try:
            module = self._import_module(plugin_file)
            plugin_class = getattr(module, "Plugin", None)
            if plugin_class is None or not issubclass(plugin_class, PluginBase):
                return None

            plugin_instance = plugin_class()
            plugin_instance.on_load()
            self.loaded_plugins[plugin_name] = plugin_instance

            registry = self._load_registry()
            registry[plugin_name] = True
            self._save_registry(registry)

            return plugin_instance
        except Exception:
            return None

    def unload(self, plugin_name: str) -> bool:
        plugin = self.loaded_plugins.get(plugin_name)
        if not plugin:
            return False
        plugin.on_unload()
        del self.loaded_plugins[plugin_name]

        registry = self._load_registry()
        registry[plugin_name] = False
        self._save_registry(registry)
        return True

    def list_loaded(self) -> List[str]:
        return list(self.loaded_plugins.keys())

    def get_all_commands(self) -> Dict[str, Callable[[str], None]]:
        commands = {}
        for plugin in self.loaded_plugins.values():
            commands.update(plugin.register_commands())
        return commands
