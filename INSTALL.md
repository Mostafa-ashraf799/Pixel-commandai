# دليل تشغيل CommandAI (cai) — خطوة بخطوة على كل الأنظمة

هذا الدليل يغطي التثبيت والتشغيل بالتفصيل على: **Linux** (Ubuntu/Debian/Fedora/Arch/Kali)،
**macOS**، **Windows** (CMD/PowerShell)، و**Android عبر Termux**.

---

## 📋 المتطلبات العامة (لكل الأنظمة)

- Python 3.9 أو أحدث.
- pip (مدير حزم بايثون، بييجي مع Python عادة).
- Git (لتحميل المشروع لو من مستودع؛ أو تكفي فك ضغط الملف يدويًا).
- مفتاح API لمزود ذكاء اصطناعي واحد على الأقل (OpenAI, Gemini, Groq, OpenRouter, DeepSeek)، أو Ollama مثبّت محليًا كبديل مجاني بدون مفتاح.

---

## 🐧 Linux (Ubuntu / Debian / Kali)

### 1. تحقق من وجود Python

```bash
python3 --version
```

لو ظهر رقم إصدار (3.9 أو أعلى) كمّل. لو الأمر مش موجود:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git
```

### 2. فك ضغط المشروع

```bash
cd ~
unzip cai_project.zip
cd cai_project
```

(لو حمّلت المشروع من Git بدل ملف مضغوط: `git clone <repo_url> && cd cai_project`)

### 3. إنشاء بيئة افتراضية (موصى به بشدة)

بيئة افتراضية بتمنع تعارض مكتبات cai مع مكتبات بايثون تانية على جهازك.
**تأكد إنك في bash** (مش sh أو dash، عشان أمر `source` يشتغل صح):

```bash
python3 -m venv venv
source venv/bin/activate
```

هتلاحظ اسم البيئة `(venv)` ظهر في بداية سطر الأوامر — ده معناه البيئة شغّالة.
تأكد بالتنفيذ:

```bash
which python3   # المفروض يشاور على .../cai_project/venv/bin/python3
```

### 4. تثبيت المتطلبات

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. تثبيت cai كأمر نظام

```bash
pip install -e .
```

`-e` معناها "editable" — أي تعديل تعمله على كود المشروع هيظهر تأثيره فورًا من غير إعادة تثبيت.

### 6. التشغيل

```bash
cai
```

لو ظهرت رسالة `command not found: cai`، شغّله مباشرة بدون تثبيت:

```bash
python3 -m cai
```

### 7. أول إعداد داخل cai

```
cai > api add openrouter sk-or-v1-xxxxxxxxxxxxx
cai > mdl openrouter/auto
cai > status
```

### تشغيله في كل مرة بعد كده

البيئة الافتراضية بتتقفل لما تقفل الـ Terminal، فمحتاج تفعّلها تاني كل مرة:

```bash
cd ~/cai_project
source venv/bin/activate
cai
```

**لتفادي تكرار الخطوة دي:** أضف alias في ملف `~/.bashrc`:

```bash
echo 'alias cai-start="cd ~/cai_project && source venv/bin/activate && cai"' >> ~/.bashrc
source ~/.bashrc
```

وبعدها تقدر تكتب `cai-start` من أي مكان.

---

## 🐧 Linux (Fedora)

نفس خطوات Ubuntu بالظبط، الفرق الوحيد في تثبيت المتطلبات الأساسية:

```bash
sudo dnf install -y python3 python3-pip git
```

باقي الخطوات (venv, pip install, cai) مطابقة تمامًا للي فوق.

---

## 🐧 Linux (Arch)

```bash
sudo pacman -Sy python python-pip git
```

باقي الخطوات مطابقة تمامًا لقسم Ubuntu.

---

## 🍎 macOS

### 1. تثبيت Python (لو مش موجود)

macOS بييجي بنسخة Python قديمة أحيانًا أو من غيرها خالص. أسهل طريقة عبر Homebrew:

```bash
# لو مفيش Homebrew:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# بعدها:
brew install python git
```

تحقق:
```bash
python3 --version
```

### 2. فك ضغط المشروع

```bash
cd ~
unzip cai_project.zip
cd cai_project
```

### 3. بيئة افتراضية + تثبيت

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 4. التشغيل

```bash
cai
```

أو لو الأمر مش متاح:

```bash
python3 -m cai
```

### 5. الإعداد الأول

```
cai > api add openrouter sk-or-v1-xxxxxxxxxxxxx
cai > status
```

### ملاحظة خاصة بـ macOS

لو ظهر خطأ متعلق بـ `cryptography` أثناء `pip install`، ثبّت أدوات البناء أولاً:

```bash
xcode-select --install
```

ثم أعد `pip install -r requirements.txt`.

---

## 🪟 Windows (PowerShell — موصى به)

### 1. تثبيت Python

نزّل من [python.org/downloads](https://python.org/downloads) (الإصدار 3.9+).
**مهم جدًا:** أثناء التثبيت، فعّل الخيار **"Add Python to PATH"** أسفل نافذة التثبيت قبل الضغط على Install.

تحقق (افتح PowerShell):

```powershell
python --version
```

### 2. تثبيت Git (لو مش موجود)

نزّل من [git-scm.com](https://git-scm.com/download/win) وثبّته بالإعدادات الافتراضية.

### 3. فك ضغط المشروع

فك ضغط `cai_project.zip` (كليك يمين → Extract All)، أو عبر PowerShell:

```powershell
Expand-Archive -Path cai_project.zip -DestinationPath .
cd cai_project
```

### 4. السماح بتشغيل السكريبتات (مطلوب مرة واحدة فقط)

PowerShell بيمنع تشغيل بعض السكريبتات افتراضيًا لأسباب أمنية. شغّل مرة واحدة:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

اكتب `Y` لو طلب تأكيد.

### 5. بيئة افتراضية + تثبيت

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

هتلاحظ `(venv)` ظهرت في بداية السطر.

### 6. التشغيل

```powershell
cai
```

لو الأمر مش موجود:

```powershell
python -m cai
```

### 7. الإعداد الأول

```
cai > api add openrouter sk-or-v1-xxxxxxxxxxxxx
cai > status
```

### تشغيله في المرات القادمة

```powershell
cd C:\Users\<اسمك>\cai_project
.\venv\Scripts\Activate.ps1
cai
```

---

## 🪟 Windows (CMD — الطريقة التقليدية)

نفس خطوات PowerShell، بس الأوامر شكلها مختلف شوية:

### تفعيل البيئة الافتراضية

```cmd
cd C:\Users\<اسمك>\cai_project
venv\Scripts\activate.bat
```

### باقي الخطوات مطابقة

```cmd
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
cai
```

**ملاحظة:** خطوة `Set-ExecutionPolicy` مش مطلوبة في CMD، دي خاصة بـ PowerShell بس.

---

## 📱 Android (عبر Termux)

### 1. تثبيت Termux نفسه

**مهم جدًا:** حمّل Termux من **F-Droid** فقط (وليس Google Play، لأن نسخة Play Store قديمة ومتوقفة عن التحديث):

🔗 [f-droid.org/packages/com.termux](https://f-droid.org/packages/com.termux)

### 2. (اختياري لكن موصى به) تثبيت تطبيق Termux:API

من نفس مصدر F-Droid، ثبّت تطبيق **Termux:API** كمان — ده لازم عشان أوامر `phone battery`, `phone notify`... تشتغل.

### 3. افتح Termux وحدّث الحزم

```bash
pkg update -y
pkg upgrade -y
```

### 4. ثبّت Git وحمّل/انقل المشروع

لو المشروع موجود كملف zip على الهاتف (مثلاً في Downloads بعد تفعيل الوصول للتخزين):

```bash
pkg install -y git python
termux-setup-storage   # يطلب إذن الوصول لملفات الهاتف، اضغط Allow
cp ~/storage/downloads/cai_project.zip ~/
cd ~
unzip cai_project.zip
cd cai_project
```

أو لو هتحمّله من مستودع Git:

```bash
pkg install -y git python
git clone <repo_url> cai_project
cd cai_project
```

### 5. شغّل سكريبت التثبيت الجاهز

المشروع فيه سكريبت مخصص لـ Termux بيعمل كل الخطوات تلقائيًا:

```bash
bash termux_setup.sh
```

السكريبت هيعمل: تحديث pkg، تثبيت Python/Git/أدوات البناء، تثبيت Termux:API،
تثبيت مكتبات بايثون المطلوبة، وتثبيت أمر `cai` نفسه.

### 6. (بديل) التثبيت اليدوي خطوة بخطوة بدل السكريبت

```bash
pkg install -y python git clang libffi openssl rust
pkg install -y termux-api
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```

### 7. التشغيل

```bash
cai
```

### 8. الإعداد الأول

```
cai > api add openrouter sk-or-v1-xxxxxxxxxxxxx
cai > status
cai > termux        # يعرض معلومات بيئة Termux المكتشفة
```

### 9. (اختياري) تفعيل الوصول لتخزين الهاتف

لو عايز cai يوصل لملفاتك (Downloads، صور، مشاريع محفوظة على الهاتف):

```bash
termux-setup-storage
```

هيظهر طلب إذن Android — اضغط **Allow**. بعدها جرّب:

```
cai > storage
```

### 10. تشغيله في المرات القادمة

افتح تطبيق Termux، واكتب:

```bash
cd ~/cai_project
cai
```

**نصيحة:** لو عايز تفتح cai بضغطة واحدة، ثبّت **Termux:Widget** (من F-Droid برضه)
وأنشئ shortcut بيشغّل الأمرين اللي فوق.

---

## ❓ حل المشاكل الشائعة (كل الأنظمة)

### "command not found: cai" أو "cai is not recognized"

الحل الأسرع دايمًا: شغّله عبر بايثون مباشرة بدل الأمر المختصر:

```bash
python3 -m cai        # Linux/macOS/Termux
python -m cai         # Windows
```

### فشل تثبيت `cryptography` أو مكتبة تانية

- **Linux:** `sudo apt install -y build-essential libssl-dev libffi-dev python3-dev`
- **macOS:** `xcode-select --install`
- **Termux:** `pkg install -y clang libffi openssl rust`
- **Windows:** نزّل [Visual C++ Build Tools](https://visualstudio.microsoft.com/visual-cpp-build-tools/)

### "لا يوجد API key مضبوط"

```
cai > api add <provider> <your_key>
```

الـ providers المدعومة: `openai`, `gemini`, `groq`, `openrouter`, `deepseek`, `ollama` (بدون مفتاح).

### "externally-managed-environment" عند pip install (Ubuntu 23.04+/Debian 12+)

معناها إن الـ venv مش مفعّلة فعليًا وبتحاول تثبت على نظام التشغيل مباشرة. تأكد إنك نفّذت:

```bash
source venv/bin/activate
```

وتحقق إنها شغّالة فعلاً بـ:

```bash
which python3   # لازم يشاور جوه مجلد venv/bin، مش /usr/bin
```

لو لسه المشكلة موجودة رغم تفعيل venv، ده معناه إنك مش فعلاً جوه بيئة bash عادية
(مثلاً بتستخدم sh أو إحدى أدوات الأتمتة). كحل أخير فقط (مش موصى به دائمًا):

```bash
pip install -r requirements.txt --break-system-packages
```

### عايز تستخدم بدون إنترنت أو بدون مفتاح API مدفوع

ثبّت [Ollama](https://ollama.com) على جهازك (مجاني ومحلي بالكامل):

```bash
# بعد تثبيت Ollama وتشغيله:
cai > provider ollama
cai > mdl llama3.2
```

من الهاتف (Termux)، اربط بجهاز Ollama شغّال على نفس شبكة الـ Wi-Fi:

```
cai > ollama connect http://192.168.1.10:11434
cai > provider ollama
```

### البيئة الافتراضية اختفت بعد إعادة تشغيل الجهاز

طبيعي — البيئة الافتراضية (venv) لازم تتفعّل يدويًا في كل جلسة Terminal جديدة:

```bash
source venv/bin/activate      # Linux/macOS/Termux
.\venv\Scripts\Activate.ps1    # Windows PowerShell
venv\Scripts\activate.bat      # Windows CMD
```

---

## 🔄 التحديث لاحقًا

من داخل cai نفسه:

```
cai > run pip install --upgrade -e .
```

أو لو نزّلت نسخة zip جديدة، فك ضغطها فوق المجلد القديم (أو في مجلد جديد) وأعد خطوات التثبيت.
