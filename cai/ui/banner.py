"""
Banner
------
شاشة البداية الخاصة بـ CommandAI (cai) كما هي محددة في مواصفات المشروع.
"""

import platform
import sys

from cai.config.config_manager import ConfigManager
from cai.providers.provider_manager import ProviderManager


def detect_shell() -> str:
    if platform.system() == "Windows":
        return "PowerShell"
    return "Bash"


def render_banner(config: ConfigManager, providers: ProviderManager) -> str:
    os_name = platform.system()
    os_display = {
        "Linux": "Linux",
        "Windows": "Windows",
        "Darwin": "macOS",
    }.get(os_name, os_name)

    py_version = ".".join(map(str, sys.version_info[:3]))
    status = providers.status()

    lines = [
        "═══════════════════════════════════════",
        "         Pixel CommandAI",
        "═══════════════════════════════════════",
        "",
        f"Version : {config.get('version')}",
        f"OS      : {os_display}",
        f"Shell   : {detect_shell()}",
        f"Python  : {py_version}",
        "",
        f"Provider : {status['provider']}",
        f"Model    : {status['model']}",
        "",
        f"Mode : {config.get('mode').capitalize()}",
        "",
        (
            "Ready ✅"
            if status["configured"]
            else (
                "⚠️  لم يتم تسجيل الدخول بعد. استخدم: signup أو login"
                if status["provider"] == "pixel"
                else "⚠️  لم يتم ضبط API key بعد. استخدم: api add <provider> <key>"
            )
        ),
        "",
        "Type help to show commands.",
        "",
    ]
    return "\n".join(lines)
