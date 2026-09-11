"""
File Manager
------------
عمليات إدارة الملفات: نسخ، نقل، حذف، إعادة تسمية، بحث، ضغط، فك ضغط،
ونظام Trash/Restore بسيط بدل الحذف النهائي المباشر (لتقليل المخاطر).
"""

import os
import shutil
import time
import zipfile
from pathlib import Path
from typing import List, Optional


class FileManager:
    def __init__(self, trash_dir: Optional[str] = None):
        self.trash_dir = Path(trash_dir or os.path.expanduser("~/.cai/trash"))
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    # ---------- عمليات أساسية ----------

    def copy(self, src: str, dst: str) -> str:
        src_path, dst_path = Path(src), Path(dst)
        if src_path.is_dir():
            shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
        else:
            dst_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_path, dst_path)
        return f"تم نسخ {src} إلى {dst}"

    def move(self, src: str, dst: str) -> str:
        shutil.move(src, dst)
        return f"تم نقل {src} إلى {dst}"

    def rename(self, path: str, new_name: str) -> str:
        p = Path(path)
        new_path = p.parent / new_name
        p.rename(new_path)
        return f"تم إعادة تسمية {path} إلى {new_path}"

    def delete(self, path: str, permanent: bool = False) -> str:
        """حذف آمن افتراضيًا (نقل لسلة المهملات) إلا لو طُلب حذف نهائي صراحة."""
        p = Path(path)
        if not p.exists():
            return f"المسار غير موجود: {path}"

        if permanent:
            if p.is_dir():
                shutil.rmtree(p)
            else:
                p.unlink()
            return f"تم الحذف النهائي: {path}"

        timestamp = int(time.time())
        trashed_name = f"{p.name}.{timestamp}"
        trashed_path = self.trash_dir / trashed_name
        shutil.move(str(p), str(trashed_path))
        return f"تم نقل {path} إلى سلة المهملات (يمكن استرجاعه)."

    def restore(self, trashed_name: str, restore_to: str) -> str:
        trashed_path = self.trash_dir / trashed_name
        if not trashed_path.exists():
            return f"لم يتم العثور على '{trashed_name}' في سلة المهملات."
        shutil.move(str(trashed_path), restore_to)
        return f"تم الاسترجاع إلى {restore_to}"

    def list_trash(self) -> List[str]:
        return [p.name for p in self.trash_dir.iterdir()]

    def empty_trash(self) -> str:
        count = 0
        for item in self.trash_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()
            count += 1
        return f"تم تفريغ سلة المهملات ({count} عنصر)."

    # ---------- بحث ----------

    def search(self, root: str, pattern: str, max_results: int = 200) -> List[str]:
        results = []
        root_path = Path(root)
        for path in root_path.rglob(pattern):
            results.append(str(path))
            if len(results) >= max_results:
                break
        return results

    # ---------- ضغط / فك ضغط ----------

    def compress(self, source: str, output_zip: str) -> str:
        source_path = Path(source)
        with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            if source_path.is_dir():
                for file in source_path.rglob("*"):
                    if file.is_file():
                        zf.write(file, file.relative_to(source_path.parent))
            else:
                zf.write(source_path, source_path.name)
        return f"تم ضغط {source} إلى {output_zip}"

    def extract(self, zip_path: str, output_dir: str) -> str:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(output_dir)
        return f"تم فك ضغط {zip_path} إلى {output_dir}"
