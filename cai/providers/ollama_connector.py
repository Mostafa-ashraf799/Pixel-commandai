"""
Ollama Connector
------------------
في بيئة الهاتف (Termux)، تشغيل نموذج LLM محليًا غالبًا غير عملي (موارد
محدودة)، فالسيناريو الشائع هو: Ollama شغال على جهاز تاني (لابتوب/سيرفر
منزلي على نفس الشبكة)، والهاتف بيتصل بيه عن بُعد.

هذا الملف يوفر اكتشافًا تلقائيًا: يجرب localhost الأول (لو المستخدم فعلاً
مثبّت Ollama جوه Termux نفسه أو على كمبيوتر عادي)، ولو فشل يجرب عنوان
بعيد محفوظ في الإعدادات (مثال: http://192.168.1.10:11434).
"""

from typing import List, Optional

try:
    import requests
except ImportError:
    requests = None


class OllamaConnector:
    def __init__(self, config):
        self.config = config

    def _is_reachable(self, base_url: str, timeout: float = 2.0) -> bool:
        if requests is None:
            return False
        try:
            resp = requests.get(f"{base_url}/api/tags", timeout=timeout)
            return resp.status_code == 200
        except Exception:
            return False

    def discover(self) -> Optional[str]:
        """
        يحاول بالترتيب: localhost، ثم أي عنوان بعيد محفوظ في الإعدادات
        (remote_ollama_url)، ويرجع أول base_url شغّال فعليًا أو None.
        """
        local_url = "http://localhost:11434"
        if self._is_reachable(local_url):
            return local_url

        remote_url = self.config.get("remote_ollama_url")
        if remote_url and self._is_reachable(remote_url):
            return remote_url

        return None

    def set_remote_url(self, url: str) -> str:
        url = url.rstrip("/")
        reachable = self._is_reachable(url)
        self.config.set("remote_ollama_url", url)
        status = "✅ تم الاتصال بنجاح" if reachable else "⚠️ تم الحفظ لكن تعذّر الوصول الآن"
        return f"{status}: {url}"

    def list_remote_models(self, base_url: str) -> List[str]:
        if requests is None:
            return []
        try:
            resp = requests.get(f"{base_url}/api/tags", timeout=10)
            data = resp.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception:
            return []

    def render_status(self) -> str:
        discovered = self.discover()
        if not discovered:
            remote = self.config.get("remote_ollama_url", "")
            hint = f"\nآخر عنوان بعيد محفوظ: {remote} (غير متاح حاليًا)" if remote else ""
            return (
                "❌ لا يوجد Ollama متاح (لا محليًا ولا عبر عنوان بعيد محفوظ).\n"
                "استخدم: ollama connect <http://IP:11434> للاتصال بجهاز على نفس الشبكة."
                f"{hint}"
            )

        models = self.list_remote_models(discovered)
        source = "محلي" if "localhost" in discovered else "بعيد"
        return f"✅ Ollama متاح ({source}): {discovered}\nالنماذج المتاحة: {', '.join(models) if models else '(لا يمكن جلبها)'}"
