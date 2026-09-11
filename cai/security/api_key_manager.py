"""
API Key Manager
---------------
يدير مفاتيح الـ API لكل الـ Providers (OpenAI, Gemini, Groq, OpenRouter... إلخ).
- إضافة / تعديل / حذف / اختبار / تبديل مفاتيح.
- التخزين مشفّر محليًا باستخدام مفتاح مشتق من جهاز المستخدم (Fernet).

ملاحظة: التشفير هنا يحمي من القراءة العرضية للملف على القرص،
لكنه ليس بديلاً عن Secret Manager حقيقي في بيئات إنتاج حساسة.
"""

import json
import os
import base64
import hashlib
from pathlib import Path
from typing import Dict, Optional

try:
    from cryptography.fernet import Fernet
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False


class APIKeyManager:
    SUPPORTED_PROVIDERS = [
        "openai", "gemini", "groq", "openrouter", "ollama",
        "anthropic", "deepseek", "local",
    ]

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.keys_path = self.base_dir / "keys.enc"
        self._fernet = self._load_or_create_key() if _HAS_CRYPTO else None
        self._keys: Dict[str, Dict[str, str]] = self._load_keys()

    # ---------- تشفير ----------

    def _machine_seed(self) -> bytes:
        seed_source = f"{os.path.expanduser('~')}-cai-secret"
        return hashlib.sha256(seed_source.encode()).digest()

    def _load_or_create_key(self) -> "Fernet":
        key_file = self.base_dir / ".secret.key"
        if key_file.exists():
            key = key_file.read_bytes()
        else:
            key = base64.urlsafe_b64encode(self._machine_seed())
            key_file.write_bytes(key)
            try:
                os.chmod(key_file, 0o600)
            except OSError:
                pass
        return Fernet(key)

    def _load_keys(self) -> Dict[str, Dict[str, str]]:
        if not self.keys_path.exists():
            return {}
        try:
            raw = self.keys_path.read_bytes()
            if self._fernet:
                raw = self._fernet.decrypt(raw)
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return {}

    def _save_keys(self) -> None:
        raw = json.dumps(self._keys, ensure_ascii=False).encode("utf-8")
        if self._fernet:
            raw = self._fernet.encrypt(raw)
        self.keys_path.write_bytes(raw)
        try:
            os.chmod(self.keys_path, 0o600)
        except OSError:
            pass

    # ---------- عمليات عامة ----------

    def add_key(self, provider: str, api_key: str, label: str = "default") -> None:
        provider = provider.lower()
        self._keys.setdefault(provider, {})[label] = api_key
        self._save_keys()

    def remove_key(self, provider: str, label: str = "default") -> bool:
        provider = provider.lower()
        if provider in self._keys and label in self._keys[provider]:
            del self._keys[provider][label]
            self._save_keys()
            return True
        return False

    def get_key(self, provider: str, label: str = "default") -> Optional[str]:
        # لو مش موجود في التخزين، جرّب متغيرات البيئة كـ fallback
        provider = provider.lower()
        stored = self._keys.get(provider, {}).get(label)
        if stored:
            return stored
        env_name = f"{provider.upper()}_API_KEY"
        return os.environ.get(env_name)

    def list_providers(self) -> Dict[str, list]:
        return {p: list(labels.keys()) for p, labels in self._keys.items()}

    def has_key(self, provider: str, label: str = "default") -> bool:
        return self.get_key(provider, label) is not None
