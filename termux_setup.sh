#!/data/data/com.termux/files/usr/bin/bash
# ==========================================================
# سكريبت تثبيت CommandAI (cai) على Termux
# ==========================================================
# الاستخدام:
#   pkg install -y git python
#   git clone <repo_url> cai_project && cd cai_project
#   bash termux_setup.sh
# ==========================================================

set -e

echo "🚀 بدء تثبيت CommandAI (cai) على Termux..."
echo ""

# 1. تحديث الحزم الأساسية
echo "📦 تحديث pkg..."
pkg update -y

# 2. تثبيت المتطلبات الأساسية (Python + Git + build tools للمكتبات اللي تحتاج compile)
echo "📦 تثبيت Python وGit..."
pkg install -y python git clang libffi openssl rust

# 3. تثبيت Termux:API (اختياري لكن موصى به بشدة)
echo "📱 تثبيت Termux:API (لأدوات الهاتف: بطارية، إشعارات، موقع...)"
pkg install -y termux-api || echo "⚠️ فشل تثبيت termux-api، تقدر تكمل بدونه وتثبته لاحقًا."

# 4. إعداد الوصول للتخزين (يطلب إذن Android)
echo ""
echo "🔒 لو عايز cai يوصل لملفاتك (Downloads، صور، مشاريع...)، شغّل الأمر ده وافق على الإذن:"
echo "    termux-setup-storage"
echo ""

# 5. تثبيت متطلبات بايثون
echo "🐍 تثبيت مكتبات بايثون..."
pip install --upgrade pip
pip install -r requirements.txt

# 6. تثبيت الحزمة نفسها كأمر نظام
echo "⚙️ تثبيت أمر cai..."
pip install -e .

echo ""
echo "✅ التثبيت اكتمل بنجاح!"
echo ""
echo "الخطوات التالية:"
echo "  1. شغّل: cai"
echo "  2. اضبط مفتاح API: api add openrouter <your_key>"
echo "  3. لو عايز تستخدم Ollama من جهاز تاني على نفس الشبكة:"
echo "     ollama connect http://<IP_الجهاز_التاني>:11434"
echo ""
