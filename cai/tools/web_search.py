"""
Web Search Tool
----------------
يسمح للـ Agent بالبحث في الويب أثناء التخطيط أو الإجابة على أسئلة تحتاج
معلومات حديثة (مثال: "do install latest nodejs LTS" أو "ابحث عن حل لخطأ معين").

يستخدم DuckDuckGo HTML endpoint (لا يحتاج API key)، وقابل للاستبدال
لاحقًا بأي مزود بحث آخر (Tavily, SerpAPI...) بنفس الواجهة.
"""

import re
from dataclasses import dataclass
from typing import List, Optional

try:
    import requests
except ImportError:
    requests = None

from cai.providers.provider_manager import ProviderManager
from cai.providers.base_provider import ChatMessage


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str


class WebSearchTool:
    SEARCH_URL = "https://html.duckduckgo.com/html/"

    def __init__(self, provider_manager: Optional[ProviderManager] = None):
        self.provider_manager = provider_manager

    def search(self, query: str, max_results: int = 5) -> List[SearchResult]:
        if requests is None:
            return []
        try:
            resp = requests.post(
                self.SEARCH_URL,
                data={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (CommandAI cai-agent)"},
                timeout=15,
            )
            html = resp.text
            results = []

            # Parsing بسيط بدون مكتبات خارجية إضافية (regex محكوم لبنية DuckDuckGo HTML)
            blocks = re.findall(
                r'<a rel="nofollow" class="result__a" href="([^"]+)">(.*?)</a>.*?'
                r'<a class="result__snippet".*?>(.*?)</a>',
                html,
                re.DOTALL,
            )
            for url, title, snippet in blocks[:max_results]:
                clean_title = re.sub(r"<.*?>", "", title).strip()
                clean_snippet = re.sub(r"<.*?>", "", snippet).strip()
                results.append(SearchResult(title=clean_title, url=url, snippet=clean_snippet))

            return results
        except Exception:
            return []

    def search_and_summarize(self, query: str, max_results: int = 5) -> str:
        """يبحث ثم يلخص النتائج عبر الـ AI بلغة طبيعية مناسبة للعرض في التيرمنال."""
        results = self.search(query, max_results=max_results)
        if not results:
            return "لم يتم العثور على نتائج (أو لا يوجد اتصال إنترنت)."

        if not self.provider_manager:
            lines = [f"- {r.title}\n  {r.url}\n  {r.snippet}" for r in results]
            return "\n\n".join(lines)

        context = "\n\n".join(f"العنوان: {r.title}\nالرابط: {r.url}\nملخص: {r.snippet}" for r in results)
        messages = [
            ChatMessage(
                role="system",
                content="لخص نتائج البحث التالية بشكل عملي ومباشر يجيب على سؤال المستخدم. "
                        "اذكر أهم رابط أو رابطين فقط في النهاية.",
            ),
            ChatMessage(role="user", content=f"سؤال المستخدم: {query}\n\nنتائج البحث:\n{context}"),
        ]
        response = self.provider_manager.chat(messages, temperature=0.3, max_tokens=800)
        return response.content if response.ok else "\n\n".join(f"- {r.title}: {r.url}" for r in results)
