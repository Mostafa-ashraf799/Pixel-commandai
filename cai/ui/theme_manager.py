"""
Theme Manager
-------------
يدير ألوان الواجهة داخل التيرمنال عبر ANSI escape codes.
الثيمات المتاحة: Dark, Light, Cyberpunk, Matrix, Hacker.
"""

from dataclasses import dataclass


@dataclass
class ThemeColors:
    primary: str
    accent: str
    success: str
    warning: str
    danger: str
    muted: str
    reset: str = "\033[0m"


THEMES = {
    "dark": ThemeColors(
        primary="\033[97m", accent="\033[36m", success="\033[32m",
        warning="\033[33m", danger="\033[31m", muted="\033[90m",
    ),
    "light": ThemeColors(
        primary="\033[30m", accent="\033[34m", success="\033[32m",
        warning="\033[33m", danger="\033[31m", muted="\033[37m",
    ),
    "cyberpunk": ThemeColors(
        primary="\033[95m", accent="\033[96m", success="\033[92m",
        warning="\033[93m", danger="\033[91m", muted="\033[35m",
    ),
    "matrix": ThemeColors(
        primary="\033[32m", accent="\033[92m", success="\033[32m",
        warning="\033[92m", danger="\033[31m", muted="\033[32m",
    ),
    "hacker": ThemeColors(
        primary="\033[92m", accent="\033[90m", success="\033[92m",
        warning="\033[33m", danger="\033[91m", muted="\033[90m",
    ),
}


class ThemeManager:
    def __init__(self, theme_name: str = "dark"):
        self.set_theme(theme_name)

    def set_theme(self, theme_name: str) -> bool:
        theme_name = theme_name.lower()
        if theme_name not in THEMES:
            return False
        self.current_name = theme_name
        self.colors = THEMES[theme_name]
        return True

    def list_themes(self):
        return list(THEMES.keys())

    def colorize(self, text: str, kind: str = "primary") -> str:
        color = getattr(self.colors, kind, self.colors.primary)
        return f"{color}{text}{self.colors.reset}"

    def success(self, text: str) -> str:
        return self.colorize(text, "success")

    def warning(self, text: str) -> str:
        return self.colorize(text, "warning")

    def danger(self, text: str) -> str:
        return self.colorize(text, "danger")

    def accent(self, text: str) -> str:
        return self.colorize(text, "accent")

    def muted(self, text: str) -> str:
        return self.colorize(text, "muted")
