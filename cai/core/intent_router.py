"""
Intent Router (AI Command Understanding)
-------------------------------------------
الميزة دي هي قلب فلسفة "مش لازم تحفظ أوامر cai". بدل ما المستخدم يكتب
"do X" أو "git commit Y" بالظبط، يقدر يكتب أي جملة طبيعية زي:
    "ارفعلي التعديلات دي على github"
    "install docker"
    "fix my network"
    "show me what's using all my cpu"

والنظام يحدد النية (intent) المناسبة ويحولها لأمر cai الفعلي المطابق،
قبل ما يلجأ لمحادثة AI عامة كحل أخير.

هذا يعمل كطبقة "قبل" الـ CommandRouter العادي: لو النية واضحة (بثقة عالية)
يرجع أمر cai مباشر جاهز للتنفيذ، ولو مش واضح يسيب الأمر يمر للمحادثة العادية.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class IntentMatch:
    command: str          # الأمر النهائي المكافئ بصيغة cai (مثال: "pkg install docker")
    confidence: float      # 0.0 - 1.0
    matched_intent: str    # اسم النية المكتشفة، للتوضيح للمستخدم


# كل نية عندها كلمات مفتاحية (عربي/إنجليزي) + قالب الأمر الناتج
INTENT_RULES: List[Tuple[str, List[str], str]] = [
    ("install_package",
     [r"\binstall\b", r"\bنصب\b", r"\bثبت\b", r"\bحمل\b"],
     "pkg install {target}"),

    ("git_push",
     [r"\bpush\b", r"\bارفع\b", r"\bرفع\b.*(github|جيت هاب|git)"],
     "git push"),

    ("git_commit",
     [r"\bcommit\b", r"\bاحفظ\b.*(تعديلات|تغييرات)"],
     "git commit {target}"),

    ("git_status",
     [r"\bgit status\b", r"\bحالة.*(git|المستودع)"],
     "git"),

    ("fix_network",
     [r"\bfix.*network\b", r"\bاصلح.*(شبكة|نت)\b", r"\bmy internet.*(down|not working)"],
     "net"),

    ("show_resources",
     [r"\b(cpu|ram|memory).*(usage|using)\b", r"\bمين.*(بياكل|بيستهلك).*(cpu|رامات|رام)",
      r"\bshow.*resources\b"],
     "dash"),

    ("scan_host",
     [r"\bscan\b.*(port|host)", r"\bافحص\b.*(بورت|سيرفر|هوست)"],
     "scan {target}"),

    ("explain_command",
     [r"\bwhat does\b.*\bdo\b", r"\bايه معنى\b", r"\bاشرحلي\b"],
     "exp {target}"),

    ("docker_ps",
     [r"\brunning containers\b", r"\bالكونتينرز.*(شغالة|شغاله)"],
     "docker ps"),

    ("write_code",
     [r"\bwrite (me )?(a |an )?(code|function|script)\b", r"\bاكتبلي.*(كود|دالة|فانكشن)"],
     "code {target}"),
]


class IntentRouter:
    def detect(self, user_input: str) -> Optional[IntentMatch]:
        text = user_input.strip()
        lowered = text.lower()

        for intent_name, patterns, template in INTENT_RULES:
            for pattern in patterns:
                if re.search(pattern, lowered):
                    target = self._extract_target(text, pattern)
                    command = template.format(target=target) if "{target}" in template else template
                    confidence = 0.85 if target or "{target}" not in template else 0.6
                    return IntentMatch(command=command.strip(), confidence=confidence, matched_intent=intent_name)

        return None

    def _extract_target(self, text: str, matched_pattern: str) -> str:
        """استخراج مبسط للهدف: بياخد آخر كلمة/كلمتين مهمين من الجملة كـ fallback بسيط."""
        # إزالة كلمات الأمر الشائعة عشان ما تفضلش في الـ target
        noise_words = {
            "install", "please", "for", "me", "the", "a", "an", "نصب", "ثبت",
            "حمل", "لو", "سمحت", "من", "فضلك", "على", "commit", "push",
        }
        words = [w for w in re.split(r"\s+", text) if w.lower() not in noise_words]
        return " ".join(words[-3:]) if words else ""

    def suggest_command(self, user_input: str, min_confidence: float = 0.6) -> Optional[str]:
        match = self.detect(user_input)
        if match and match.confidence >= min_confidence:
            return match.command
        return None
