"""
Built-in Tools Registration
------------------------------
يسجّل الأدوات الفعلية الموجودة في cai (FileManager, GitAssistant,
ExecutionEngine...) كـ Tools حقيقية قابلة للاستدعاء المباشر من الـ AI،
بدل ما تفضل مجرد كلاسات بايثون تُستدعى فقط من CommandRouter.

هذا هو الجسر بين "الأدوات القديمة" (v1/v2) و"Tool Calling الحقيقي" (v3).
"""

from cai.tools_registry.tool_registry import ToolRegistry, ToolParameter
from cai.tools.files.file_manager import FileManager
from cai.tools.git.git_assistant import GitAssistant
from cai.engine.execution_engine import ExecutionEngine
from cai.tools.network.network_tools import NetworkTools
from cai.tools.dashboard import Dashboard


def register_builtin_tools(
    registry: ToolRegistry,
    files: FileManager,
    git: GitAssistant,
    engine: ExecutionEngine,
    net: NetworkTools,
    dashboard: Dashboard,
) -> None:

    # ---------- File Tools ----------

    def read_file(path: str) -> str:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()[:8000]  # حد أقصى لتفادي إغراق الـ context

    registry.register(
        name="read_file",
        description="يقرأ محتوى ملف نصي من القرص ويرجعه.",
        parameters=[ToolParameter("path", "string", "المسار الكامل أو النسبي للملف")],
        handler=read_file,
    )

    def write_file(path: str, content: str) -> str:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"تم الكتابة في {path}"

    registry.register(
        name="write_file",
        description="يكتب محتوى جديد في ملف (يستبدل المحتوى الحالي بالكامل).",
        parameters=[
            ToolParameter("path", "string", "مسار الملف"),
            ToolParameter("content", "string", "المحتوى الجديد الكامل"),
        ],
        handler=write_file,
        requires_confirmation=True,
    )

    registry.register(
        name="copy_file",
        description="ينسخ ملف أو مجلد من مكان لمكان.",
        parameters=[
            ToolParameter("src", "string", "المسار المصدر"),
            ToolParameter("dst", "string", "المسار الهدف"),
        ],
        handler=files.copy,
    )

    registry.register(
        name="move_file",
        description="ينقل أو يعيد تسمية ملف أو مجلد.",
        parameters=[
            ToolParameter("src", "string", "المسار الحالي"),
            ToolParameter("dst", "string", "المسار الجديد"),
        ],
        handler=files.move,
    )

    registry.register(
        name="delete_file",
        description="يحذف ملف أو مجلد (ينقله لسلة مهملات cai بشكل افتراضي قابل للاسترجاع).",
        parameters=[
            ToolParameter("path", "string", "المسار المطلوب حذفه"),
            ToolParameter("permanent", "boolean", "حذف نهائي بدون رجعة", required=False),
        ],
        handler=files.delete,
        requires_confirmation=True,
    )

    registry.register(
        name="search_files",
        description="يبحث عن ملفات بنمط معين (مثال: *.py) داخل مجلد.",
        parameters=[
            ToolParameter("root", "string", "المجلد الجذر للبحث"),
            ToolParameter("pattern", "string", "نمط البحث، مثال: *.py"),
        ],
        handler=files.search,
    )

    # ---------- Git Tools ----------

    def git_status_tool() -> str:
        result = git.status()
        return result.stdout or result.stderr

    registry.register(
        name="git_status",
        description="يعرض حالة مستودع Git الحالي (تغييرات غير محفوظة، الفرع الحالي).",
        parameters=[],
        handler=git_status_tool,
    )

    def git_commit_tool(message: str) -> str:
        results = git.commit(message)
        return "\n".join(r.stdout or r.stderr for r in results)

    registry.register(
        name="git_commit",
        description="يعمل commit لكل التغييرات الحالية برسالة معينة.",
        parameters=[ToolParameter("message", "string", "رسالة الـ commit")],
        handler=git_commit_tool,
        requires_confirmation=True,
    )

    def git_push_tool() -> str:
        result = git.push()
        return result.stdout or result.stderr

    registry.register(
        name="git_push",
        description="يرفع الـ commits الحالية للـ remote.",
        parameters=[],
        handler=git_push_tool,
        requires_confirmation=True,
    )

    # ---------- Execution Tool (للأوامر العامة غير المغطاة بأداة مخصصة) ----------

    def run_shell_command(command: str) -> str:
        result = engine.run(command)
        return result.stdout or result.stderr or "(بدون مخرجات)"

    registry.register(
        name="run_shell_command",
        description="ينفذ أمر Terminal مباشر على نظام المستخدم. استخدمها فقط لو مفيش أداة أدق متاحة.",
        parameters=[ToolParameter("command", "string", "الأمر الكامل المطلوب تنفيذه")],
        handler=run_shell_command,
        requires_confirmation=True,
    )

    # ---------- Network Tool ----------

    def ping_host(host: str) -> str:
        result = net.ping(host, count=3)
        return result.stdout or result.stderr

    registry.register(
        name="ping_host",
        description="يفحص إمكانية الوصول لعنوان/سيرفر عبر ping.",
        parameters=[ToolParameter("host", "string", "اسم النطاق أو الـ IP")],
        handler=ping_host,
    )

    # ---------- System Tool ----------

    def get_system_status() -> str:
        return dashboard.render()

    registry.register(
        name="get_system_status",
        description="يرجع حالة النظام الحالية (CPU, RAM, Disk, أهم العمليات).",
        parameters=[],
        handler=get_system_status,
    )
