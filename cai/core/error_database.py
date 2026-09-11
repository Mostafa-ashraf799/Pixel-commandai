"""
Error Knowledge Database
---------------------------
بيحفظ كل خطأ يحصل مع حله لو اتلاقى (سواء عبر quick_fix معروف أو عبر AI)،
وبعد فترة استخدام يبقى عنده "قاعدة معرفة" شخصية بأكثر الأخطاء اللي
بتواجه المستخدم تحديدًا وأسرع طريقة لحلها — بدل ما يسأل الـ AI نفس
السؤال كل مرة من الصفر.

يفرّق بين نوع الخطأ (عبر hash مبسط لرسالة الخطأ بعد تطبيع القيم المتغيرة
زي الأرقام والمسارات) عشان "same error, different path" يتصنف كخطأ واحد.
"""

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Dict, List, Optional


class ErrorDatabase:
    def __init__(self, base_dir: str = None):
        import os
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = self.base_dir / "error_knowledge.json"
        self._db: Dict[str, dict] = self._load()

    def _load(self) -> Dict[str, dict]:
        if not self.db_path.exists():
            return {}
        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _save(self) -> None:
        with open(self.db_path, "w", encoding="utf-8") as f:
            json.dump(self._db, f, indent=2, ensure_ascii=False)

    def _normalize(self, error_message: str) -> str:
        """يزيل الأجزاء المتغيرة (أرقام، مسارات، أوقات) عشان نفس الخطأ بمتغيرات مختلفة يتجمع تحت نفس المفتاح."""
        text = error_message.lower()
        text = re.sub(r"/[\w\-./]+", "<path>", text)
        text = re.sub(r"\d+", "<num>", text)
        text = re.sub(r"0x[0-9a-f]+", "<hex>", text)
        return text.strip()

    def _fingerprint(self, error_message: str) -> str:
        normalized = self._normalize(error_message)
        return hashlib.sha1(normalized.encode()).hexdigest()[:12]

    def record_error(self, command: str, error_message: str) -> str:
        fingerprint = self._fingerprint(error_message)
        entry = self._db.setdefault(fingerprint, {
            "normalized": self._normalize(error_message),
            "sample_message": error_message[:300],
            "occurrences": 0,
            "commands": [],
            "solutions": [],
            "first_seen": time.time(),
        })
        entry["occurrences"] += 1
        entry["last_seen"] = time.time()
        if command not in entry["commands"]:
            entry["commands"].append(command)
        self._save()
        return fingerprint

    def record_solution(self, fingerprint: str, solution: str, worked: bool = True) -> None:
        entry = self._db.get(fingerprint)
        if not entry:
            return
        entry["solutions"].append({"text": solution, "worked": worked, "ts": time.time()})
        self._save()

    def lookup(self, error_message: str) -> Optional[dict]:
        """يبحث لو نفس الخطأ (بعد التطبيع) حصل قبل كده وعنده حل معروف."""
        fingerprint = self._fingerprint(error_message)
        return self._db.get(fingerprint)

    def best_known_solution(self, error_message: str) -> Optional[str]:
        entry = self.lookup(error_message)
        if not entry or not entry["solutions"]:
            return None
        # نفضّل آخر حل نجح فعليًا
        successful = [s for s in entry["solutions"] if s.get("worked")]
        if successful:
            return successful[-1]["text"]
        return entry["solutions"][-1]["text"]

    def most_frequent_errors(self, limit: int = 10) -> List[dict]:
        return sorted(self._db.values(), key=lambda e: -e["occurrences"])[:limit]

    def render_report(self, limit: int = 10) -> str:
        frequent = self.most_frequent_errors(limit)
        if not frequent:
            return "لا توجد أخطاء مسجّلة بعد."

        lines = [f"أكثر {len(frequent)} أخطاء تكرارًا:"]
        for entry in frequent:
            has_solution = "✅ يوجد حل معروف" if entry["solutions"] else "❓ بدون حل مسجّل بعد"
            lines.append(f"  ({entry['occurrences']}x) {entry['sample_message'][:80]}")
            lines.append(f"      {has_solution}")
        return "\n".join(lines)
