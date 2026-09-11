"""
Example Plugin: Hello Plugin
------------------------------
مثال بسيط يوضح طريقة كتابة Plugin لـ CommandAI.
لتفعيله: انسخ هذا الملف إلى ~/.cai/plugins/hello.py ثم شغّل داخل cai:
    plug load hello
    hello
"""

from cai.plugins.plugin_manager import PluginBase


class Plugin(PluginBase):
    name = "hello"
    description = "مثال بسيط لإضافة أمر جديد لـ cai"
    version = "1.0.0"

    def register_commands(self):
        return {
            "hello": self.say_hello,
        }

    def say_hello(self, args: str) -> None:
        print(f"👋 أهلاً من الإضافة hello! (args: {args})")

    def on_load(self) -> None:
        print("تم تحميل إضافة hello بنجاح.")
