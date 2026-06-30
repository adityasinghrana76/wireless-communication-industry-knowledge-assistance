import hashlib
from urllib.parse import parse_qs, unquote, urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.models import Source


class SearchService:
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()

    async def search(self, query: str, max_results: int) -> list[dict]:
        if self.settings.tavily_api_key:
            results = await self._tavily(query, max_results)
            if results:
                return results
        return await self._fallback_results(query, max_results)

    async def _tavily(self, query: str, max_results: int) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={"api_key": self.settings.tavily_api_key, "query": query, "max_results": max_results},
                )
                response.raise_for_status()
                payload = response.json()
        except (httpx.HTTPError, ValueError):
            return []
        return [
            {"url": item["url"], "title": item.get("title"), "summary": item.get("content")}
            for item in payload.get("results", [])
            if item.get("url")
        ]

    async def _fallback_results(self, query: str, max_results: int) -> list[dict]:
        results = await self._duckduckgo(query, max_results)
        if results:
            return results
        return self._curated_results(query, max_results)

    async def _duckduckgo(self, query: str, max_results: int) -> list[dict]:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            )
        }
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(8.0, connect=3.0),
                follow_redirects=True,
                headers=headers,
            ) as client:
                response = await client.get("https://duckduckgo.com/html/", params={"q": query})
                response.raise_for_status()
        except httpx.HTTPError:
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        items: list[dict] = []
        seen_urls: set[str] = set()
        for result in soup.select(".result"):
            link = result.select_one("a.result__a")
            if not link:
                continue
            url = self._clean_result_url(link.get("href") or "")
            if not url or url in seen_urls:
                continue
            snippet = result.select_one(".result__snippet")
            summary = " ".join(snippet.get_text(" ").split()) if snippet else None
            items.append(
                {
                    "url": url,
                    "title": " ".join(link.get_text(" ").split()) or url,
                    "summary": summary or f"Search result for: {query}",
                }
            )
            seen_urls.add(url)
            if len(items) >= max_results:
                break
        return items

    def _clean_result_url(self, url: str) -> str:
        if not url:
            return ""
        parsed = urlparse(url)
        if parsed.query:
            redirect = parse_qs(parsed.query).get("uddg")
            if redirect:
                return unquote(redirect[0])
        return url

    def _curated_results(self, query: str, max_results: int) -> list[dict]:
        catalog = [
            {
                "url": "https://www.ericsson.com/en/ran",
                "title": "Ericsson Radio Access Network portfolio",
                "summary": "Vendor portfolio covering 5G RAN, radios, antennas, Massive MIMO, and network modernization.",
            },
            {
                "url": "https://www.nokia.com/networks/mobile-networks/radio-access-networks-ran/",
                "title": "Nokia Radio Access Networks",
                "summary": "Nokia portfolio information for mobile RAN, AirScale radios, baseband, and 5G network deployments.",
            },
            {
                "url": "https://www.qualcomm.com/products/technology/modems/5g",
                "title": "Qualcomm 5G modem and RF systems",
                "summary": "Qualcomm product information for 5G modem-RF platforms used across devices and network equipment.",
            },
            {
                "url": "https://www.keysight.com/us/en/solutions/5g.html",
                "title": "Keysight 5G test and measurement solutions",
                "summary": "Test, validation, and measurement solutions for 5G, Open RAN, RF, and wireless network equipment.",
            },
            {
                "url": "https://www.3gpp.org/technologies/5g-system-overview",
                "title": "3GPP 5G system overview",
                "summary": "Standards body overview of 5G system architecture, radio access, and technology evolution.",
            },
        ]
        query_terms = {term.lower() for term in query.split() if len(term) > 2}

        def score(item: dict) -> int:
            haystack = f"{item['title']} {item['summary']}".lower()
            return sum(1 for term in query_terms if term in haystack)

        ranked = sorted(catalog, key=score, reverse=True)
        return ranked[:max_results]

    def persist_results(self, results: list[dict]) -> list[Source]:
        sources: list[Source] = []
        for result in results:
            url = result["url"]
            url_hash = hashlib.sha256(url.encode()).hexdigest()
            source = self.db.query(Source).filter(Source.url == url).one_or_none()
            if source is None:
                source = Source(
                    url=url,
                    url_hash=url_hash,
                    title=result.get("title"),
                    summary=result.get("summary"),
                    raw_text=result.get("summary"),
                    credibility_score=60,
                )
                self.db.add(source)
            sources.append(source)
        self.db.commit()
        return sources


def clean_html(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()
    return " ".join(soup.get_text(" ").split())
