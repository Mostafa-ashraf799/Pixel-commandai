"""
Plugin Marketplace
---------------------
توسعة لـ PluginManager (v2) بإضافة مفهوم "Registry" خارجي: مصدر مركزي
(ملف JSON بسيط، يمكن استضافته على GitHub لاحقًا) يحتوي فهرس الإضافات
المتاحة، وكل إضافة فيها رابط تحميل مباشر (raw URL لملف .py).

هذا تصميم "registry-lite" مناسب لمرحلة مبكرة: بدون سيرفر باكيند حقيقي
أو نظام مصادقة، لكنه يوفر أوامر install/search/update/publish بمعناها
الحقيقي (تنزيل فعلي، فحص فعلي للتحديثات) بدل واجهة زخرفية فقط.
"""

import json
import time
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    requests = None

from cai.plugins.plugin_manager import PluginManager


DEFAULT_REGISTRY_URL = "https://raw.githubusercontent.com/example/cai-plugins-registry/main/registry.json"


class PluginMarketplace:
    def __init__(self, plugin_manager: PluginManager, registry_url: str = DEFAULT_REGISTRY_URL):
        self.plugin_manager = plugin_manager
        self.registry_url = registry_url
        self._registry_cache: Optional[List[dict]] = None
        self.installed_meta_path = plugin_manager.plugins_dir / "installed_meta.json"

    def _fetch_registry(self) -> List[dict]:
        if self._registry_cache is not None:
            return self._registry_cache

        if requests is None:
            return []

        try:
            resp = requests.get(self.registry_url, timeout=10)
            if resp.status_code == 200:
                self._registry_cache = resp.json().get("plugins", [])
                return self._registry_cache
        except Exception:
            pass

        return []

    def search(self, query: str) -> List[dict]:
        registry = self._fetch_registry()
        query_lower = query.lower()
        return [
            p for p in registry
            if query_lower in p.get("name", "").lower() or query_lower in p.get("description", "").lower()
        ]

    def _load_installed_meta(self) -> Dict[str, dict]:
        if not self.installed_meta_path.exists():
            return {}
        try:
            with open(self.installed_meta_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save_installed_meta(self, meta: Dict[str, dict]) -> None:
        with open(self.installed_meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)

    def install(self, plugin_name: str) -> str:
        registry = self._fetch_registry()
        entry = next((p for p in registry if p.get("name") == plugin_name), None)

        if not entry:
            return f"لم يتم العثور على '{plugin_name}' في الـ Registry. جرّب: plugin search {plugin_name}"

        if requests is None:
            return "مكتبة requests غير متاحة، لا يمكن التنزيل."

        try:
            resp = requests.get(entry["download_url"], timeout=15)
            if resp.status_code != 200:
                return f"فشل تنزيل الإضافة (HTTP {resp.status_code})."

            plugin_path = self.plugin_manager.plugins_dir / f"{plugin_name}.py"
            plugin_path.write_text(resp.text, encoding="utf-8")

            meta = self._load_installed_meta()
            meta[plugin_name] = {
                "version": entry.get("version", "unknown"),
                "installed_at": time.time(),
                "source": entry["download_url"],
            }
            self._save_installed_meta(meta)

            return f"تم تثبيت '{plugin_name}' بنجاح. استخدم: plug load {plugin_name}"
        except Exception as e:
            return f"فشل التثبيت: {e}"

    def check_updates(self) -> List[str]:
        registry = self._fetch_registry()
        installed = self._load_installed_meta()
        updates_available = []

        for name, meta in installed.items():
            remote_entry = next((p for p in registry if p.get("name") == name), None)
            if remote_entry and remote_entry.get("version") != meta.get("version"):
                updates_available.append(name)

        return updates_available

    def update(self, plugin_name: str) -> str:
        installed = self._load_installed_meta()
        if plugin_name not in installed:
            return f"الإضافة '{plugin_name}' غير مثبّتة عبر Marketplace."
        return self.install(plugin_name)  # نفس منطق التثبيت يقوم بالتحديث (استبدال الملف)

    def publish_instructions(self, local_plugin_path: str) -> str:
        """
        النشر الفعلي على Registry مركزي يحتاج بنية استضافة/مصادقة خارج نطاق
        هذا الكود، فبدل محاكاة عملية وهمية، نرجع تعليمات واضحة وصادقة.
        """
        path = Path(local_plugin_path)
        if not path.exists():
            return f"الملف غير موجود: {local_plugin_path}"

        return (
            f"لنشر '{path.name}' على المجتمع:\n"
            f"1. ارفع الملف لمستودع GitHub عام (أو أضفه لمستودع cai-plugins-registry).\n"
            f"2. أضف سطرًا في registry.json يتضمن: name, description, version, download_url (raw link).\n"
            f"3. افتح Pull Request على مستودع الـ Registry.\n"
            f"(هذا الإصدار من cai لا يدعم نشرًا تلقائيًا مباشرًا بدون سيرفر مركزي مُدار.)"
        )

    def render_search_results(self, query: str) -> str:
        results = self.search(query)
        if not results:
            return f"لا توجد نتائج لـ '{query}' (أو تعذّر الوصول للـ Registry)."

        lines = [f"نتائج البحث عن '{query}':"]
        for r in results:
            lines.append(f"  {r['name']} (v{r.get('version', '?')}) — {r.get('description', '')}")
        return "\n".join(lines)
