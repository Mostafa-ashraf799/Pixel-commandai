# CommandAI (cai) — v3

مساعد ذكاء اصطناعي احترافي يعمل بالكامل داخل الـ Terminal، مبني بـ Python
على بنية معمارية حقيقية: Dependency Injection, Event-Driven Architecture,
وTool Calling فعلي (function calling) بدل توليد أوامر نصية فقط.

## التشغيل السريع

```bash
pip install -r requirements.txt
python -m cai
```

```
cai > api add openrouter <your_api_key>
cai > mdl openrouter/auto
cai > agent اقرأ ملف app.py وقولي فيه إيه
```

---

## 🏗️ البنية المعمارية (v3)

### Dependency Injection Container
كل خدمة (`config`, `logger`, `providers`, `memory`, `event_bus`...) مسجّلة
مرة واحدة في `Container` (انظر `cai/core/di/bootstrap.py`)، وأي جزء من
البرنامج بيطلبها عبر `container.resolve("service_name")` بدل ما ينشئها بنفسه.
هذا يسمح باستبدال أي خدمة بنسخة اختبار (mock) بسهولة، ويمنع التكرار.

### Event Bus
بدل التواصل المباشر بين الوحدات، أي حدث مهم (`CommandExecuted`,
`TaskStarted`, `PluginLoaded`, `ProviderChanged`, `FileEdited`...) يُنشر
عبر `EventBus`، وأي جزء مهتم (Logger, Session, Telemetry) يستمع له باستقلالية
تامة عن الناشر. انظر `cai/core/events/`.

### Tool Registry (Tool Calling حقيقي)
الفرق الجوهري عن الإصدارات السابقة: الـ AI دلوقتي بيستقبل قائمة أدوات
حقيقية بصيغة JSON Schema (`cai/tools_registry/`) وينادي عليها مباشرة
(`read_file`, `write_file`, `git_commit`, `run_shell_command`...) بدل ما
يولّد نص Terminal يتفسّر لاحقًا. استخدمه عبر أمر `agent`.

### Context Manager
يجمع صورة شاملة قبل أي طلب AI: المحادثة الأخيرة، المجلد الحالي، حالة Git،
نظام التشغيل، إصدار Python، الملفات المفتوحة مؤخرًا، آخر الأوامر، وآخر
الأخطاء. انظر `cai/core/context_manager.py`.

### Prompt Templates
كل الـ prompts دلوقتي في ملفات Markdown مستقلة تحت `prompts/` (`planner.md`,
`coder.md`, `reviewer.md`, `linux.md`, `windows.md`, `git.md`, `security.md`...)
بدل ما تكون مدمجة في الكود، فتقدر تعدّل شخصية أي دور بدون لمس بايثون.

---

## 🎭 AI Roles & Profiles

**Roles** (`role`): أدوار متخصصة (Coder, Reviewer, Debugger, Architect,
Linux Expert, Windows Expert, Security Expert, Git Expert)، كل واحد
بـ prompt وtemperature مناسبين له.

```
cai > role linux_expert اشرحلي فرق apt وapt-get
cai > role auto عندي conflict في git، أعمل إيه؟   # يختار الدور تلقائيًا
```

**Profiles** (`profile`): يغيّر شخصية الـ AI كاملة حسب نوع المستخدم
(Developer, Pentester, Python Developer, DevOps, Student) — يؤثر على
أسلوب الشرح ووضع الصلاحيات الافتراضي.

```
cai > profile pentester
cai > profile student
```

---

## 🔧 Multi-Session, Jobs, Workflow, Macro

**Sessions**: `session list | switch | resume | archive`
**Background Jobs**: `bg <cmd>` يشغّل في الخلفية، `jobs` يعرض القائمة،
`fg <id>` ينتظر النتيجة، `kill <id>` يوقفه.
**Workflow**: سير عمل قابل للبناء والحفظ والتصدير:
```
cai > workflow create deploy_flow "نشر تلقائي"
cai > workflow add-step deploy_flow shell "git pull"
cai > workflow add-step deploy_flow shell "docker compose up -d --build"
cai > workflow run deploy_flow
cai > workflow export deploy_flow deploy_flow.json
```
**Macro**: تسجيل أوامر حقيقية أثناء الاستخدام:
```
cai > macro record
... (استخدام عادي) ...
cai > macro stop
cai > macro save my_routine
cai > macro run my_routine
```

---

## 🧩 Marketplace & Config Layers

**Marketplace**: `plug install/search/update/publish <name>` (registry-lite
عبر ملف JSON مركزي على GitHub، انظر `cai/plugins/marketplace.py`).

**Layered Config**: 4 طبقات (`session` > `workspace` > `project` > `global`):
```
cai > config                          # يعرض كل الطبقات
cai > config get monthly_budget_usd   # يوضح من أي طبقة جاءت القيمة
cai > config set mode expert project  # يحفظ في .cai.json (يُشارك عبر Git)
```

---

## 🛡️ ميزات أمان واستقرار

- **Secrets Scanner** (`secrets`) + فحص تلقائي قبل أي `git push`.
- **Pre-Deploy Health Check** (`predeploy`).
- **Snapshot/Undo** (`snapshot`, `undo <file>`) — نسخة قبل أي تعديل.
- **Error Database** (`errors`) — قاعدة معرفة تراكمية لأكثر الأخطاء تكرارًا وحلولها.
- **Crash Recovery** — عند إعادة تشغيل cai بعد تعطل غير متوقع، يقترح استرجاع آخر جلسة.
- **Offline Mode** (`offline`) — يكتشف انقطاع الإنترنت ويقترح التحويل لـ Ollama.
- **Auto Update + Rollback** — `UpdateSystem.update()` / `.rollback()`.
- **Telemetry اختياري** (`telemetry on/off`) — بيانات محلية بالكامل، شفافة تمامًا.
- **Terminal Recorder** — تسجيل الجلسة الكاملة كملف نصي للمراجعة/المشاركة.

---

## 🩺 أوامر تشخيصية

```
cai > doctor     # فحص شامل لصحة النظام (Provider, إنترنت, موارد, أسرار, أدوات)
cai > whoami     # ملخص سريع للحالة الحالية (Profile, Mode, Provider, Session)
cai > metrics    # إحصائيات الأداء + تقرير التكلفة
```

---

## 📋 جدول الأوامر الكامل (62 أمر)

| الفئة | الأوامر |
|---|---|
| **Agent حقيقي** | `agent`, `do`, `team`, `role` |
| **الكود** | `code`, `edit`, `dbg`, `rev`, `analyze` |
| **النظام** | `run`, `git`, `docker`, `ssh`, `pkg`, `net`, `scan`, `dash` |
| **الذكاء الاصطناعي** | `mdl`, `provider`, `api`, `search`, `role` |
| **الأتمتة** | `template`, `script`, `workflow`, `macro`, `alias` |
| **الأمان** | `secrets`, `predeploy`, `snapshot`, `undo` |
| **الجلسات/المهام** | `session`, `jobs`, `fg`, `bg`, `kill` |
| **التخصيص** | `profile`, `theme`, `config`, `cfg` |
| **التشخيص** | `doctor`, `whoami`, `metrics`, `errors`, `offline`, `cost` |
| **عام** | `status`, `mem`, `his`, `context`, `docgen`, `plug`, `voice`, `clear`, `exit` |

---

## 📊 إحصائيات المشروع

- **99 ملف Python | ~7,660 سطر كود**
- **9 ملفات Prompt Templates** قابلة للتعديل بدون كود
- **62 أمر** متصل بالكامل عبر Command Router
- **DI Container + Event Bus + Tool Registry** كطبقة معمارية أساسية

## هيكل المشروع

```
cai/
├── core/
│   ├── di/                  Container + Bootstrap
│   ├── events/               EventBus + الأحداث القياسية + المستمعون
│   ├── context_manager.py     سياق شامل للـ AI
│   ├── prompt_loader.py       تحميل prompts/*.md
│   ├── intent_router.py       فهم النية الطبيعية
│   ├── auto_context.py        اكتشاف نوع المشروع تلقائيًا
│   ├── cost_tracker.py        تتبع تكلفة AI
│   ├── snapshot_manager.py    نسخ احتياطية + Undo
│   ├── error_database.py      قاعدة معرفة الأخطاء
│   ├── crash_recovery.py      استرداد بعد الأعطال
│   ├── terminal_recorder.py   تسجيل الجلسة الكاملة
│   ├── offline_mode.py        اكتشاف انقطاع الإنترنت
│   ├── telemetry.py           إحصائيات اختيارية شفافة
│   ├── alias_manager.py       اختصارات مخصصة
│   └── update_system.py       تحديث + Rollback
├── tools_registry/            Tool Registry الحقيقي + الأدوات المسجّلة
├── agent/
│   ├── planner.py / agent_executor.py   (v1: خطة نصية)
│   ├── multi_agent.py                    (v2: فريق وكلاء)
│   ├── tool_calling_agent.py              (v3: Tool Calling حقيقي)
│   └── workflow_templates.py              قوالب مشاريع جاهزة
├── roles/                     AI Roles (Coder, Reviewer, Linux Expert...)
├── profiles/                  Profiles (Developer, Pentester, Student...)
├── jobs/                      Background Jobs
├── workflows/                 Workflow قابل للبناء والتصدير
├── macros/                    Macro Recorder
├── providers/                 طبقة موحدة لكل مزودي AI
├── security/                  API Keys + Permissions + Secrets Scanner
├── memory/                    Memory + History + Multi-Session
├── tools/                     Git/Docker/SSH/Network/Package/Files/...
├── plugins/                   Plugin System + Marketplace
├── config/                    Config عادي + Layered Config
└── ui/                        Shell + Banner + Theme
prompts/                       كل الـ AI prompts كملفات Markdown مستقلة
```

---

## 📱 دعم Termux (Android)

cai بيكتشف تلقائيًا لو شغال داخل Termux، ويتكيّف مع الفروقات الجوهرية:
بدون `sudo`، `pkg` بدل `apt`، مسارات Android، والوصول المقيّد للتخزين.

### التثبيت على Termux

```bash
pkg install -y git python
git clone <repo_url> cai_project && cd cai_project
bash termux_setup.sh
```

السكريبت بيثبّت Python، Git، أدوات البناء اللازمة لمكتبات زي `cryptography`،
ويحاول تثبيت `termux-api` (اختياري لكن موصى به)، ثم يثبّت cai نفسه.

### الأوامر الخاصة بـ Termux

| الأمر | الوظيفة |
|---|---|
| `termux` | معلومات المنصة (مدير الحزم، حالة Termux:API، التخزين) |
| `termux api` | ملخص حالة الجهاز عبر Termux:API |
| `storage` | يعرض مجلدات تخزين الهاتف المتاحة (downloads, dcim, shared...) |
| `storage downloads` | المسار الكامل لمجلد التنزيلات (لفتح مشاريع موجودة عليه) |
| `phone battery` | حالة البطارية الفعلية |
| `phone notify <رسالة>` | إشعار Android حقيقي |
| `phone vibrate` | اهتزاز الجهاز |
| `phone toast <رسالة>` | رسالة سريعة على الشاشة |
| `phone clipboard` | قراءة حافظة النظام |
| `phone speak <نص>` | نطق نص بصوت الجهاز (TTS) |
| `phone location` | الموقع الجغرافي الحالي (GPS) |
| `ollama status` | يفحص هل Ollama متاح محليًا أو عن بُعد |
| `ollama connect <http://IP:11434>` | ربط بجهاز Ollama على نفس الشبكة |
| `sync export <path>` | تصدير الإعدادات والاختصارات لملف JSON |
| `sync import <path>` | استيرادها على جهاز تاني |

### الوصول لتخزين الهاتف

```bash
termux-setup-storage   # مرة واحدة فقط، بيطلب إذن Android صريح
```

بعدها `storage` هيوريك كل المجلدات المتاحة، بما فيها اكتشاف تلقائي لأي
مشاريع بايثون/Node موجودة في مجلد Downloads (عن طريق البحث عن
`requirements.txt`, `package.json`, `.git`).

### Git داخل Termux

أوامر `git` (clone, commit, push, pull, branch...) تشتغل بنفس الطريقة
تمامًا — Termux بيوفر Git الحقيقي، فمفيش أي طبقة تكيّف إضافية مطلوبة هنا.

### Ollama محليًا أو عن بُعد

تشغيل نموذج LLM كامل جوه الهاتف غالبًا غير عملي (استهلاك بطارية وذاكرة
عالٍ)، فالسيناريو المُوصى به: شغّل Ollama على لابتوب/سيرفر منزلي على نفس
شبكة الـ Wi-Fi، وبعدها من الهاتف:

```
cai > ollama connect http://192.168.1.10:11434
cai > provider ollama
```

`cai` بيكتشف تلقائيًا لو فيه Ollama محلي شغال الأول، ولو مش موجود يستخدم
آخر عنوان بعيد محفوظ.

### مزامنة الإعدادات (اختيارية)

```
# على الكمبيوتر
cai > sync export cai_config_bundle.json

# انقل الملف عبر Syncthing / Google Drive / scp للهاتف، بعدين على Termux:
cai > sync import cai_config_bundle.json
```

بيُزامَن: الـ Provider/Model المفضّل، الثيم، اللغة، الميزانية الشهرية،
والاختصارات (aliases). **لا تُزامَن عمدًا**: مفاتيح API (كل جهاز يضبطها
بنفسه لأسباب أمنية)، والـ Sessions/History/Memory (بيانات محلية بطبيعتها).
