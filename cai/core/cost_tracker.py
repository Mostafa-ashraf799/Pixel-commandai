"""
Cost Tracker
------------
ميزة مهمة لأي حد بيستخدم AI APIs بشكل يومي: تتبع استهلاك التوكنز
والتكلفة التقريبية لكل Provider/Model، مع تنبيه لو تجاوزت حد معين شهريًا.

الأسعار هنا تقريبية (USD لكل مليون توكن) ومبنية على قيم شائعة معروفة،
وقابلة للتحديث يدويًا من المستخدم عبر update_pricing() لو الأسعار اتغيرت.
"""

import json
import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# تكلفة تقريبية لكل مليون توكن (input, output) بالدولار
DEFAULT_PRICING: Dict[str, Dict[str, tuple]] = {
    "openai": {
        "gpt-4o": (2.5, 10.0),
        "gpt-4o-mini": (0.15, 0.6),
    },
    "gemini": {
        "gemini-2.5-pro": (1.25, 5.0),
        "gemini-2.5-flash": (0.075, 0.3),
    },
    "groq": {
        "llama-3.3-70b-versatile": (0.59, 0.79),
    },
    "openrouter": {
        "openrouter/auto": (0.5, 1.5),  # تقديري، يختلف حسب الموديل المُوجَّه إليه فعليًا
    },
    "deepseek": {
        "deepseek-chat": (0.27, 1.1),
    },
    "ollama": {
        "*": (0.0, 0.0),  # محلي ومجاني بالكامل
    },
}


@dataclass
class UsageRecord:
    ts: float
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_usd: float


@dataclass
class CostSummary:
    total_cost_usd: float = 0.0
    total_prompt_tokens: int = 0
    total_completion_tokens: int = 0
    by_provider: Dict[str, float] = field(default_factory=dict)
    record_count: int = 0


class CostTracker:
    def __init__(self, base_dir: str = None, monthly_budget_usd: Optional[float] = None):
        self.base_dir = Path(base_dir or os.path.expanduser("~/.cai"))
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.usage_path = self.base_dir / "usage.jsonl"
        self.pricing = {k: dict(v) for k, v in DEFAULT_PRICING.items()}
        self.monthly_budget_usd = monthly_budget_usd

    def update_pricing(self, provider: str, model: str, input_price: float, output_price: float) -> None:
        self.pricing.setdefault(provider.lower(), {})[model] = (input_price, output_price)

    def _lookup_price(self, provider: str, model: str) -> tuple:
        provider_table = self.pricing.get(provider.lower(), {})
        if model in provider_table:
            return provider_table[model]
        if "*" in provider_table:
            return provider_table["*"]
        return (0.0, 0.0)  # موديل غير معروف السعر -> نعتبره 0 بدل تخمين خاطئ

    def record(self, provider: str, model: str, prompt_tokens: int, completion_tokens: int) -> UsageRecord:
        input_price, output_price = self._lookup_price(provider, model)
        cost = (prompt_tokens / 1_000_000) * input_price + (completion_tokens / 1_000_000) * output_price

        entry = UsageRecord(
            ts=time.time(), provider=provider, model=model,
            prompt_tokens=prompt_tokens, completion_tokens=completion_tokens,
            cost_usd=round(cost, 6),
        )

        with open(self.usage_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry.__dict__, ensure_ascii=False) + "\n")

        return entry

    def _load_records(self, since_ts: Optional[float] = None) -> List[UsageRecord]:
        if not self.usage_path.exists():
            return []
        records = []
        with open(self.usage_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if since_ts is None or data["ts"] >= since_ts:
                        records.append(UsageRecord(**data))
                except (json.JSONDecodeError, TypeError):
                    continue
        return records

    def summary(self, since_ts: Optional[float] = None) -> CostSummary:
        records = self._load_records(since_ts)
        summary = CostSummary(record_count=len(records))
        for r in records:
            summary.total_cost_usd += r.cost_usd
            summary.total_prompt_tokens += r.prompt_tokens
            summary.total_completion_tokens += r.completion_tokens
            summary.by_provider[r.provider] = summary.by_provider.get(r.provider, 0.0) + r.cost_usd
        summary.total_cost_usd = round(summary.total_cost_usd, 4)
        summary.by_provider = {k: round(v, 4) for k, v in summary.by_provider.items()}
        return summary

    def current_month_summary(self) -> CostSummary:
        now = time.localtime()
        start_of_month = time.mktime((now.tm_year, now.tm_mon, 1, 0, 0, 0, 0, 0, 0))
        return self.summary(since_ts=start_of_month)

    def budget_alert(self) -> Optional[str]:
        if not self.monthly_budget_usd:
            return None
        month_summary = self.current_month_summary()
        if month_summary.total_cost_usd >= self.monthly_budget_usd:
            return (
                f"⚠️ تجاوزت الميزانية الشهرية المحددة (${self.monthly_budget_usd}): "
                f"استهلكت ${month_summary.total_cost_usd} حتى الآن."
            )
        remaining_pct = 100 - (month_summary.total_cost_usd / self.monthly_budget_usd * 100)
        if remaining_pct <= 10:
            return f"⚠️ اقتربت من حد الميزانية الشهرية (${month_summary.total_cost_usd} / ${self.monthly_budget_usd})."
        return None

    def render_report(self) -> str:
        month = self.current_month_summary()
        all_time = self.summary()

        lines = [
            "── Cost Report ─────────────────",
            f"هذا الشهر : ${month.total_cost_usd}  ({month.record_count} طلب)",
            f"إجمالي     : ${all_time.total_cost_usd}  ({all_time.record_count} طلب)",
            "",
            "التوزيع حسب Provider (كل الأوقات):",
        ]
        for provider, cost in sorted(all_time.by_provider.items(), key=lambda x: -x[1]):
            lines.append(f"  {provider:<15} ${cost}")

        alert = self.budget_alert()
        if alert:
            lines.append("")
            lines.append(alert)

        return "\n".join(lines)
