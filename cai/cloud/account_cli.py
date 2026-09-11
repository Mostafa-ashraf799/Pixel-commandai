"""
Account CLI (Pixel CommandAI)
-----------------------------
أوامر بسيطة مستقلة لإدارة الحساب: تسجيل، دخول، خروج، وعرض الحالة.
نفس منطق الأوامر المدمجة في command_router.py، متاحة هنا للاستخدام
المباشر أو الاختبار:

    python -m cai.cloud.account_cli login
    python -m cai.cloud.account_cli signup
    python -m cai.cloud.account_cli whoami
    python -m cai.cloud.account_cli logout
"""

import getpass
import json
import sys
import urllib.request

from cai.providers.provider_manager import PIXEL_SUPABASE_URL, PIXEL_SUPABASE_ANON_KEY
from cai.cloud.auth_manager import AuthManager, AuthError


def _get_auth() -> AuthManager:
    return AuthManager(PIXEL_SUPABASE_URL, PIXEL_SUPABASE_ANON_KEY)


def _detect_country() -> str | None:
    try:
        req = urllib.request.Request(f"{PIXEL_SUPABASE_URL}/functions/v1/detect-country")
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("country_code")
    except Exception:
        return None


def cmd_signup() -> int:
    auth = _get_auth()
    print("إنشاء حساب Pixel CommandAI جديد")
    full_name = input("الاسم بالكامل: ").strip()
    email = input("البريد الإلكتروني: ").strip()
    password = getpass.getpass("كلمة المرور: ")
    phone = input("رقم الهاتف [اختياري]: ").strip() or None
    purpose = input("الاستخدام الأساسي (developer/devops/security/student/other) [اختياري]: ").strip() or None

    country = _detect_country()
    if country:
        confirm = input(f"دولتك المكتشفة: {country} — صح؟ (Enter للتأكيد، أو اكتب رمز تاني): ").strip().upper()
        if confirm:
            country = confirm
    else:
        country = input("رمز الدولة (مثال: EG, US, SA) [اختياري]: ").strip().upper() or None

    try:
        result = auth.sign_up(
            email, password,
            country_code=country, full_name=full_name or None, phone=phone, usage_purpose=purpose,
        )
        if result.get("access_token"):
            print("تم إنشاء الحساب وتسجيل الدخول بنجاح. خطتك الحالية: Free")
        else:
            print("تم إنشاء الحساب! افتح بريدك الإلكتروني واضغط على رابط التأكيد، وبعدين استخدم: login")
        return 0
    except AuthError as e:
        print(f"فشل إنشاء الحساب: {e}")
        return 1


def cmd_login() -> int:
    auth = _get_auth()
    email = input("البريد الإلكتروني: ").strip()
    password = getpass.getpass("كلمة المرور: ")
    try:
        auth.sign_in(email, password)
        print("تم تسجيل الدخول بنجاح.")
        return 0
    except AuthError as e:
        print(f"فشل تسجيل الدخول: {e}")
        return 1


def cmd_logout() -> int:
    auth = _get_auth()
    auth.sign_out()
    print("تم تسجيل الخروج.")
    return 0


def cmd_whoami() -> int:
    auth = _get_auth()
    if not auth.is_logged_in():
        print("لم يتم تسجيل الدخول. استخدم: pixel-cai login")
        return 1
    user = auth.current_user()
    email = (user or {}).get("email", "غير معروف")
    print(f"مسجل الدخول كـ: {email}")
    return 0


_COMMANDS = {
    "signup": cmd_signup,
    "login": cmd_login,
    "logout": cmd_logout,
    "whoami": cmd_whoami,
}


def main() -> int:
    if len(sys.argv) < 2 or sys.argv[1] not in _COMMANDS:
        print("الاستخدام: python -m cai.cloud.account_cli [signup|login|logout|whoami]")
        return 1
    return _COMMANDS[sys.argv[1]]()


if __name__ == "__main__":
    sys.exit(main())
