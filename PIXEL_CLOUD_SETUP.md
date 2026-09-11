# Pixel CommandAI — Cloud Layer Setup

هذا الملف يشرح الطبقة الجديدة اللي اتضافت فوق كود CommandAI الأصلي
عشان تحوّله لمنتج SaaS (Pixel CommandAI). الكود ده **نسخة منفصلة تمامًا**
عن الريبو الأصلي المعروض للبيع — مش بيشاركه أي تاريخ commits ولا مسار.

## اللي اتضاف

```
cai/cloud/
  ├── __init__.py
  ├── auth_manager.py      # تسجيل دخول/خروج عبر Supabase Auth REST API
  ├── pixel_provider.py    # Provider جديد يوجّه الطلبات عبر Edge Function
  └── account_cli.py       # أوامر signup/login/logout/whoami مستقلة
```

بالإضافة لتعديلين بسيطين على الكود الحالي:
- `cai/providers/provider_manager.py` — إضافة `pixel` كخيار provider
- `cai/config/config_manager.py` — الافتراضي بقى `pixel` بدل `openrouter`

## البنية التحتية على Supabase (مشروع: pixel-commandai)

- **project_id**: `fazjxaukksdkeztejeow`
- **project URL**: `https://fazjxaukksdkeztejeow.supabase.co`

### الجداول (تم إنشاؤها بالكامل)
- `plans` — الخطط الثلاثة (free/basic/pro) مع السعر والحصة وفترة التجديد
- `country_pricing` — معامل PPP لكل دولة (قيم تجريبية أولية — راجعها قبل الإطلاق)
- `profiles` — بيانات المستخدم وخطته الحالية
- `usage_windows` — نافذة الاستخدام الحالية (تتجدد كل 5/10 ساعات)
- `usage_events` — سجل كل طلب فعلي (تدقيق/كشف إساءة استخدام)
- `payments` — سجل المدفوعات (كريبتو حاليًا)

كل الجداول عليها Row Level Security مفعّل، والمستخدم يقدر يشوف بياناته
بس (عبر `auth.uid()`).

### Edge Function: `chat-proxy`
دي **نقطة الأمان المركزية** — الوحيدة اللي شايلة مفتاح OpenRouter.
بتعمل بالترتيب:
1. تتحقق من الـ JWT بتاع المستخدم
2. تجيب خطته وحصته الحالية من `usage_windows`
3. لو الحصة خلصت (وخطته مش soft-throttled زي Pro) → ترفض بـ 429
4. لو تمام، تبعت الطلب لـ OpenRouter بمفتاحك انت
5. تسجل الاستخدام في قاعدة البيانات
6. **تشيل اسم الموديل قبل ما ترجع الرد للمستخدم** — عشان يفضل سر داخلي

## اللي لسه محتاج تعمله بنفسك (خارج نطاق الكود)

### 1. حط أسرار OpenRouter و NOWPayments (مهم جدًا — الأداة مش هتشتغل من غيرهم)
```bash
supabase secrets set OPENROUTER_API_KEY=sk-or-v1-xxxxx --project-ref fazjxaukksdkeztejeow
supabase secrets set OPENROUTER_MODEL=minimax/minimax-m3:free --project-ref fazjxaukksdkeztejeow
supabase secrets set NOWPAYMENTS_API_KEY=<مفتاح NOWPayments> --project-ref fazjxaukksdkeztejeow
supabase secrets set NOWPAYMENTS_IPN_SECRET=<سر التحقق من الـ webhook> --project-ref fazjxaukksdkeztejeow
supabase secrets set PAYMENT_SUCCESS_URL=<رابط صفحة "تم الدفع" بتاعتك> --project-ref fazjxaukksdkeztejeow
```
أو من لوحة تحكم Supabase مباشرة: Project Settings → Edge Functions → Secrets.

كمان لازم تسجّل رابط الـ webhook في لوحة تحكم NOWPayments (أو تسيبه يتبعت
تلقائيًا مع كل فاتورة، زي ما الكود بيعمل بالفعل عبر `ipn_callback_url`):
```
https://fazjxaukksdkeztejeow.supabase.co/functions/v1/payment-webhook
```

**الموديل المحدد حاليًا: `minimax/minimax-m3:free`** (النسخة المجانية من MiniMax M3 عبر
OpenRouter). ملاحظة مهمة: النسخة `:free` من OpenRouter بتيجي بحدود Rate Limit
صارمة من عند OpenRouter نفسه (مش من عندك) — لو عدد المستخدمين زاد ممكن تواجه
رفض طلبات بكثرة. لو حصل كده، الحل هو التبديل لنسخة مدفوعة من نفس الموديل أو
موديل تاني، وده بس تغيير قيمة `OPENROUTER_MODEL` بدون أي تعديل في الكود.

### 2. استبدل الـ anon key الحقيقي
في `cai/providers/provider_manager.py`:
```python
PIXEL_SUPABASE_ANON_KEY = "REPLACE_WITH_ANON_KEY"
```
الـ anon key مش سر (آمن يترفع مع الكود) — تلاقيه في لوحة Supabase تحت
Project Settings → API → `anon` `public` key.

### 3. النظام الآن يدعم الترقية الفعلية عبر الكريبتو
Edge Functions المنشورة:
- `create-invoice` — بتحسب السعر حسب دولة المستخدم (PPP) وتنشئ فاتورة NOWPayments
- `payment-webhook` — بتستقبل تأكيد الدفع من NOWPayments (بتحقق من التوقيع HMAC-SHA512) وترقّي الخطة تلقائيًا

استخدام المستخدم:
```bash
python -m cai.cloud.payment_cli upgrade basic
python -m cai.cloud.payment_cli upgrade pro
```
هيطلع رابط دفع بـ USDT/USDC، وبمجرد التأكيد، `profiles.plan_id` بتتحدث تلقائيًا (اشتراك لمدة 30 يوم من تاريخ الدفع).

### 4. راجع أرقام `country_pricing` و `quota_tokens`
القيم الحالية **تخمينية للتجربة فقط** — راجعها بعد ما تعرف تكلفة
الموديل الفعلية من OpenRouter وبيانات PPP حقيقية.

## كيف يسجل المستخدم دخوله (تجربة حالية عبر الطرفية)

```bash
python -m cai.cloud.account_cli signup   # إنشاء حساب جديد
python -m cai.cloud.account_cli login    # تسجيل دخول
python -m cai.cloud.account_cli whoami   # عرض الحساب الحالي
python -m cai.cloud.account_cli logout   # تسجيل خروج
```

بعد تسجيل الدخول، أي استخدام عادي للأداة (`cai` بأي أمر بيستخدم AI) هيمر
تلقائيًا عبر `PixelProvider` لأنه بقى الـ provider الافتراضي.

## لوحة إدارة المستخدمين (Admin Dashboard)

الموقع فيه قسم مخفي (`#admin`) بيظهر تلقائيًا لو الحساب المسجّل دخوله
عنده `is_admin = true`، وبيعرض كل المستخدمين (الاسم، الإيميل، الهاتف،
الاستخدام، الدولة، الخطة، نسبة استهلاك الحصة، تاريخ التسجيل).

**عشان تفعّل حسابك كأدمن:**
1. اعمل `signup` بحسابك العادي أولًا (لو لسه ما عملتش)
2. من لوحة تحكم Supabase → **Table Editor** → جدول `profiles`
3. دوّر على صف بالإيميل بتاعك، وغيّر عمود `is_admin` من `false` لـ `true`

بعد كده، أي مرة تسجل دخولك من الموقع، قسم لوحة الإدارة هيظهر تلقائيًا
تحت قسم "مثال عملي" وقبل "تواصل".

## إصلاح أمني مهم (تم تلقائيًا)

اكتشفنا وصلّحنا ثغرة أمنية حقيقية: كان أي مستخدم عادي يقدر يستدعي
Supabase مباشرة (من غير ما يمر بالموقع أو الأداة) ويغيّر عمود
`plan_id` بتاعه لـ `pro` مجانًا، أو حتى يخلي نفسه أدمن! تم إصلاحها
بـ trigger على جدول `profiles` بيرفض أي تعديل على الحقول الحساسة
(`plan_id`, `plan_expires_at`, `is_admin`) لو جاي من جلسة مستخدم
عادي — مسموح بيه بس من الـ service role اللي بتستخدمه الـ Edge
Functions (زي webhook الدفع). المستخدم لسه يقدر يعدّل بياناته
العادية (الاسم، الهاتف) عادي.

## ملاحظة أمان

الوصول للبيانات محمي على مستويين: الموقع بيتأكد من `is_admin` قبل
ما يعرض القسم، **وبرضو** دالة قاعدة البيانات `get_admin_user_overview()`
بتتأكد من نفس الشرط من عند السيرفر — يعني حتى لو حد لعب في كود
الموقع نفسه من المتصفح، مش هيقدر يشوف بيانات مستخدمين تانيين غير
لو حسابه فعلًا أدمن.
