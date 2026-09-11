"""
Prompt Loader
---------------
يقرأ ملفات prompts/*.md ويوفرها كنصوص جاهزة للاستخدام، بدل ما تكون
الـ prompts مدمجة (hardcoded) داخل كل ملف بايثون كما كان في v1/v2.

الفايدة: أي حد يقدر يعدّل شخصية/سلوك الـ AI بتعديل ملف Markdown بسيط
من غير ما يلمس كود بايثون، وده أساس نظام الـ Profiles اللي جاي بعد كده.

يدعم Caching بسيط (يقرأ الملف من القرص مرة واحدة) مع إمكانية إعادة
التحميل الصريح (reload) لو المستخدم عدّل الملف أثناء التشغيل.
"""

import os
from pathlib import Path
from typing import Dict, Optional


class PromptLoader:
    def __init__(self, prompts_dir: Optional[str] = None):
        # افتراضيًا يدور على مجلد prompts/ في جذر المشروع
        default_dir = Path(__file__).resolve().parent.parent.parent / "prompts"
        self.prompts_dir = Path(prompts_dir or os.environ.get("CAI_PROMPTS_DIR", default_dir))
        self._cache: Dict[str, str] = {}

    def load(self, name: str, use_cache: bool = True) -> str:
        """
        name بدون امتداد .md، مثال: load("planner") يقرأ prompts/planner.md
        """
        if use_cache and name in self._cache:
            return self._cache[name]

        path = self.prompts_dir / f"{name}.md"
        if not path.exists():
            return ""

        content = path.read_text(encoding="utf-8").strip()
        self._cache[name] = content
        return content

    def reload(self, name: Optional[str] = None) -> None:
        if name:
            self._cache.pop(name, None)
        else:
            self._cache.clear()

    def list_available(self) -> list:
        if not self.prompts_dir.exists():
            return []
        return sorted(p.stem for p in self.prompts_dir.glob("*.md"))

    def save(self, name: str, content: str) -> str:
        """يسمح بتعديل/إنشاء prompt جديد من داخل cai نفسه."""
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
        path = self.prompts_dir / f"{name}.md"
        path.write_text(content, encoding="utf-8")
        self.reload(name)
        return f"تم حفظ القالب: {name}.md"
