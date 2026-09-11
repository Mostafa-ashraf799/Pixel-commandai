"""
Auth Manager (Pixel CommandAI)
------------------------------
يدير تسجيل دخول/خروج المستخدم عبر Supabase Auth، وتخزين الـ session
محليًا بشكل آمن. هذا الملف خاص بنسخة Pixel CommandAI (SaaS) فقط —
لا علاقة له بنظام مفاتيح الـ API المحلي في النسخة الأصلية.

الجلسة (access_token / refresh_token) بتتخزن مشفّرة في:
~/.pixel-cai/session.enc
"""

import json
import os
import base64
import hashlib
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Optional, Dict, Any

try:
    from cryptography.fernet import Fernet
    _HAS_CRYPTO = True
except ImportError:
    _HAS_CRYPTO = False


class AuthError(Exception):
    pass


class AuthManager:
    def __init__(self, supabase_url: str, supabase_anon_key: str, base_dir: str = None):
        self.supabase_url = supabase_url.rstrip("/")
        self.supabase_anon_key = supabase_anon_key
        self.base_dir = Path(base_dir or os.path.expanduser("~/.pixel-cai"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.session_path = self.base_dir / "session.enc"
        self._fernet = self._load_or_create_key() if _HAS_CRYPTO else None
        self._session: Optional[Dict[str, Any]] = self._load_session()

    # ---------- تشفير الجلسة محليًا (نفس فكرة APIKeyManager الأصلي) ----------

    def _machine_seed(self) -> bytes:
        seed_source = f"{os.path.expanduser('~')}-pixel-cai-secret"
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

    def _load_session(self) -> Optional[Dict[str, Any]]:
        if not self.session_path.exists():
            return None
        try:
            raw = self.session_path.read_bytes()
            if self._fernet:
                raw = self._fernet.decrypt(raw)
            return json.loads(raw.decode("utf-8"))
        except Exception:
            return None

    def _save_session(self, session: Dict[str, Any]) -> None:
        raw = json.dumps(session, ensure_ascii=False).encode("utf-8")
        if self._fernet:
            raw = self._fernet.encrypt(raw)
        self.session_path.write_bytes(raw)
        try:
            os.chmod(self.session_path, 0o600)
        except OSError:
            pass
        self._session = session

    def _clear_session(self) -> None:
        if self.session_path.exists():
            self.session_path.unlink()
        self._session = None

    # ---------- استدعاءات Supabase Auth REST API ----------

    def _post(self, path: str, payload: Dict[str, Any], extra_headers: Dict[str, str] = None) -> Dict[str, Any]:
        url = f"{self.supabase_url}/auth/v1{path}"
        headers = {
            "Content-Type": "application/json",
            "apikey": self.supabase_anon_key,
        }
        if extra_headers:
            headers.update(extra_headers)
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            try:
                parsed = json.loads(body)
                msg = parsed.get("error_description") or parsed.get("msg") or body
            except Exception:
                msg = body
            raise AuthError(msg)

    def sign_up(
        self,
        email: str,
        password: str,
        country_code: Optional[str] = None,
        full_name: Optional[str] = None,
        phone: Optional[str] = None,
        usage_purpose: Optional[str] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"email": email, "password": password}
        meta = {}
        if country_code:
            meta["country_code"] = country_code
        if full_name:
            meta["full_name"] = full_name
        if phone:
            meta["phone"] = phone
        if usage_purpose:
            meta["usage_purpose"] = usage_purpose
        if meta:
            payload["data"] = meta
        result = self._post("/signup", payload)
        # لو تأكيد الإيميل مفعّل في المشروع، Supabase مش بيرجّع access_token
        # فورًا — بيرجع بيانات المستخدم بس، وده طبيعي ومقصود (يمنع حسابات وهمية).
        if "access_token" in result:
            self._save_session(result)
        return result

    def sign_in(self, email: str, password: str) -> Dict[str, Any]:
        result = self._post("/token?grant_type=password", {"email": email, "password": password})
        if "access_token" not in result:
            raise AuthError("فشل تسجيل الدخول — تحقق من البريد/كلمة المرور")
        self._save_session(result)
        return result

    def sign_out(self) -> None:
        self._clear_session()

    def _refresh_if_needed(self) -> None:
        if not self._session:
            raise AuthError("لم يتم تسجيل الدخول. استخدم `pixel-cai login`.")
        expires_at = self._session.get("expires_at", 0)
        if time.time() < expires_at - 60:
            return  # still valid
        refresh_token = self._session.get("refresh_token")
        if not refresh_token:
            raise AuthError("انتهت الجلسة. سجّل الدخول مرة أخرى.")
        result = self._post("/token?grant_type=refresh_token", {"refresh_token": refresh_token})
        if "access_token" not in result:
            raise AuthError("انتهت الجلسة. سجّل الدخول مرة أخرى.")
        self._save_session(result)

    def get_access_token(self) -> str:
        self._refresh_if_needed()
        return self._session["access_token"]

    def is_logged_in(self) -> bool:
        return self._session is not None

    def current_user(self) -> Optional[Dict[str, Any]]:
        if not self._session:
            return None
        return self._session.get("user")
