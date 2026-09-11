"""
Payment CLI (Pixel CommandAI)
-----------------------------
يولّد رابط دفع بالبطاقة عبر Lemon Squeezy لترقية خطة المستخدم.
يعتمد على `create-checkout` Edge Function (منشورة على Supabase) التي
تحسب السعر النهائي حسب دولة المستخدم (PPP) وتنشئ رابط الدفع نيابة عنه
دون كشف مفتاح Lemon Squeezy على جهازه.

ملاحظة: الدفع بالعملات الرقمية (NOWPayments / create-invoice) متوقف
مؤقتًا وليس محذوفًا — الكود الخاص به لسه موجود في الخادم لو احتجت
ترجع له لاحقًا.

الاستخدام:
    python -m cai.cloud.payment_cli upgrade basic
    python -m cai.cloud.payment_cli upgrade pro
"""

import sys
import json
import urllib.request
import urllib.error

from cai.providers.provider_manager import PIXEL_SUPABASE_URL, PIXEL_SUPABASE_ANON_KEY
from cai.cloud.auth_manager import AuthManager, AuthError

VALID_PLANS = {"basic", "pro"}


def cmd_upgrade(plan_id: str) -> int:
    if plan_id not in VALID_PLANS:
        print(f"خطة غير معروفة: {plan_id}. الخطط المتاحة: {', '.join(VALID_PLANS)}")
        return 1

    auth = AuthManager(PIXEL_SUPABASE_URL, PIXEL_SUPABASE_ANON_KEY)
    if not auth.is_logged_in():
        print("لازم تسجل الدخول الأول: python -m cai.cloud.account_cli login")
        return 1

    try:
        token = auth.get_access_token()
    except AuthError as e:
        print(f"خطأ في الجلسة: {e}")
        return 1

    url = f"{PIXEL_SUPABASE_URL}/functions/v1/create-checkout"
    body = json.dumps({"plan_id": plan_id}).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="ignore")
        print(f"فشل إنشاء رابط الدفع: {raw}")
        return 1

    checkout_url = data.get("checkout_url")
    if not checkout_url:
        print(f"استجابة غير متوقعة: {data}")
        return 1

    print(f"افتح الرابط ده عشان تكمل الدفع بالبطاقة:\n{checkout_url}")
    print("خطتك هتترقّي تلقائيًا بمجرد تأكيد الدفع (عادة خلال دقائق).")
    return 0


def main() -> int:
    if len(sys.argv) < 3 or sys.argv[1] != "upgrade":
        print("الاستخدام: python -m cai.cloud.payment_cli upgrade [basic|pro]")
        return 1
    return cmd_upgrade(sys.argv[2])


if __name__ == "__main__":
    sys.exit(main())
