"""
Profiles
--------
Profile بيغيّر شخصية الـ AI بالكامل حسب نوع المستخدم: أسلوب الشرح،
مستوى التفاصيل التقنية، والتحذيرات الأمنية المفعّلة افتراضيًا.

مثال: Profile "Student" بيخلي الشرح أبسط وأطول، بينما "Pentester"
بيقلل التحذيرات الأخلاقية الزائدة ويركز على التفاصيل التقنية الدقيقة،
و"DevOps" بيركز على Infrastructure/CI/CD.

الـ Profile الحالي بيُضاف كطبقة system prompt إضافية فوق أي دور (Role)
أو prompt تاني بيُستخدم، مش بديل عنه.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class Profile:
    key: str
    display_name: str
    system_addition: str
    default_mode: str = "smart"  # يؤثر على PermissionManager الافتراضي


PROFILES: Dict[str, Profile] = {
    "developer": Profile(
        key="developer",
        display_name="Developer",
        system_addition=(
            "خاطب المستخدم كمطور محترف. لا داعي لشرح المفاهيم الأساسية للبرمجة. "
            "ركّز على الحلول العملية والكود مباشرة."
        ),
        default_mode="smart",
    ),
    "pentester": Profile(
        key="pentester",
        display_name="Pentester",
        system_addition=(
            "خاطب المستخدم كخبير اختبار اختراق يعمل في بيئة مصرّح بها قانونيًا. "
            "قدّم تفاصيل تقنية دقيقة حول أدوات وتقنيات الأمان دون مواعظ أخلاقية متكررة، "
            "لكن لا تقدّم مساعدة لأي نشاط يبدو أنه يستهدف نظامًا لا يملكه المستخدم صراحة."
        ),
        default_mode="expert",
    ),
    "python_dev": Profile(
        key="python_dev",
        display_name="Python Developer",
        system_addition=(
            "ركّز إجاباتك على بايثون تحديدًا: أفضل الممارسات (PEP8)، المكتبات القياسية "
            "والشائعة، وأنماط تصميم بايثونية (Pythonic patterns)."
        ),
        default_mode="smart",
    ),
    "devops": Profile(
        key="devops",
        display_name="DevOps Engineer",
        system_addition=(
            "ركّز على Infrastructure, CI/CD, Docker, Kubernetes, والأتمتة. "
            "افترض أن المستخدم يهتم بالموثوقية (Reliability) وقابلية التوسع (Scalability) "
            "أكثر من التفاصيل النظرية."
        ),
        default_mode="smart",
    ),
    "student": Profile(
        key="student",
        display_name="Student",
        system_addition=(
            "اشرح المفاهيم من الأساس بأسلوب تعليمي مبسّط مع أمثلة توضيحية. "
            "لا تفترض معرفة مسبقة، واشرح أي مصطلح تقني تستخدمه لأول مرة."
        ),
        default_mode="safe",
    ),
}


class ProfileManager:
    def __init__(self, active_key: str = "developer"):
        self.active_key = active_key if active_key in PROFILES else "developer"

    @property
    def active(self) -> Profile:
        return PROFILES[self.active_key]

    def set_active(self, key: str) -> bool:
        if key not in PROFILES:
            return False
        self.active_key = key
        return True

    def list_profiles(self) -> List[str]:
        return list(PROFILES.keys())

    def get(self, key: str) -> Optional[Profile]:
        return PROFILES.get(key)

    def augment_system_prompt(self, base_prompt: str) -> str:
        """يضيف توجيه الـ Profile النشط فوق أي system prompt أساسي."""
        return f"{base_prompt}\n\n[توجيه إضافي حسب البروفايل النشط: {self.active.display_name}]\n{self.active.system_addition}"

    def render_list(self) -> str:
        lines = ["البروفايلات المتاحة:"]
        for key, profile in PROFILES.items():
            marker = "✓" if key == self.active_key else " "
            lines.append(f"  [{marker}] {key:<12} — {profile.display_name}")
        return "\n".join(lines)
