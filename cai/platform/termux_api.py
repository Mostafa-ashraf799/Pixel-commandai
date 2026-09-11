"""
Termux API Bridge
--------------------
واجهة بايثون فوق أوامر Termux:API الفعلية (كل أمر منها هو CLI منفصل
بيتنصب مع حزمة termux-api، وبيتواصل مع تطبيق Termux:API على الهاتز
عبر نظام intents الخاص بأندرويد).

كل دالة هنا بترجع نتيجة JSON (أو None لو الأداة مش متاحة/فشلت)، وده
بيدي cai قدرة فعلية على التفاعل مع الهاتف: البطارية، الموقع، الإشعارات،
الحافظة، الاهتزاز، الفلاش، ومعلومات الشبكة.
"""

import json
import shutil
import subprocess
from typing import Any, Dict, List, Optional


class TermuxAPIBridge:
    def __init__(self):
        self._available = shutil.which("termux-battery-status") is not None

    def is_available(self) -> bool:
        return self._available

    def _run_json(self, command: List[str], timeout: int = 10) -> Optional[Any]:
        if not self._available:
            return None
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            if result.returncode != 0:
                return None
            return json.loads(result.stdout) if result.stdout.strip() else None
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            return None

    def _run_text(self, command: List[str], timeout: int = 10) -> Optional[str]:
        if not self._available:
            return None
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
            return result.stdout.strip() if result.returncode == 0 else None
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return None

    # ---------- معلومات الجهاز ----------

    def battery_status(self) -> Optional[Dict]:
        """يرجع {percentage, temperature, status, plugged, health}."""
        return self._run_json(["termux-battery-status"])

    def wifi_info(self) -> Optional[Dict]:
        return self._run_json(["termux-wifi-connectioninfo"])

    def telephony_info(self) -> Optional[Dict]:
        return self._run_json(["termux-telephony-deviceinfo"])

    # ---------- الموقع ----------

    def get_location(self, provider: str = "gps", timeout: int = 20) -> Optional[Dict]:
        """provider: 'gps' | 'network' | 'passive'. يحتاج إذن الموقع من المستخدم."""
        return self._run_json(["termux-location", "-p", provider], timeout=timeout)

    # ---------- إشعارات وتنبيهات ----------

    def show_notification(self, title: str, content: str, notification_id: Optional[str] = None) -> bool:
        if not self._available:
            return False
        command = ["termux-notification", "--title", title, "--content", content]
        if notification_id:
            command += ["--id", notification_id]
        try:
            subprocess.run(command, capture_output=True, timeout=10)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def vibrate(self, duration_ms: int = 300) -> bool:
        if not self._available:
            return False
        try:
            subprocess.run(["termux-vibrate", "-d", str(duration_ms)], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def toast(self, message: str) -> bool:
        """رسالة سريعة تظهر وتختفي على الشاشة."""
        if not self._available:
            return False
        try:
            subprocess.run(["termux-toast", message], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    # ---------- الحافظة (Clipboard) ----------

    def clipboard_get(self) -> Optional[str]:
        return self._run_text(["termux-clipboard-get"])

    def clipboard_set(self, text: str) -> bool:
        if not self._available:
            return False
        try:
            subprocess.run(["termux-clipboard-set"], input=text, text=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    # ---------- الفلاش / الكاميرا ----------

    def toggle_flashlight(self, on: bool) -> bool:
        if not self._available:
            return False
        try:
            subprocess.run(["termux-torch", "on" if on else "off"], capture_output=True, timeout=5)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    # ---------- نطق نصوص (Text-to-Speech) ----------

    def speak(self, text: str) -> bool:
        if not self._available:
            return False
        try:
            subprocess.run(["termux-tts-speak", text], capture_output=True, timeout=15)
            return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False

    def render_device_summary(self) -> str:
        if not self._available:
            return "Termux:API غير مثبّت. شغّل: pkg install termux-api (والتطبيق من نفس مصدر Termux)."

        lines = []
        battery = self.battery_status()
        if battery:
            lines.append(f"البطارية: {battery.get('percentage')}% ({battery.get('status')})")

        wifi = self.wifi_info()
        if wifi and wifi.get("ssid"):
            lines.append(f"شبكة Wi-Fi: {wifi.get('ssid')}")

        return "\n".join(lines) if lines else "تعذّر جلب معلومات الجهاز (تأكد من منح الأذونات لتطبيق Termux:API)."
