import hashlib

import httpx
from sqlalchemy.orm import Session

from app.models import Source
from app.services.search import clean_html


class CrawlService:
    def __init__(self, db: Session):
        self.db = db

    async def crawl_urls(self, urls: list[str], render_js: bool = False) -> list[Source]:
        # Playwright rendering can be routed here for sites that need JS.
        if render_js:
            return await self._crawl_with_playwright(urls)
        async with httpx.AsyncClient(timeout=25, follow_redirects=True) as client:
            sources = []
            for url in urls:
                response = await client.get(url)
                response.raise_for_status()
                text = clean_html(response.text)
                sources.append(self._upsert_source(url, text))
        self.db.commit()
        return sources

    async def _crawl_with_playwright(self, urls: list[str]) -> list[Source]:
        from playwright.async_api import async_playwright

        sources = []
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            for url in urls:
                await page.goto(url, wait_until="networkidle")
                text = clean_html(await page.content())
                sources.append(self._upsert_source(url, text))
            await browser.close()
        self.db.commit()
        return sources

    def _upsert_source(self, url: str, text: str) -> Source:
        source = self.db.query(Source).filter(Source.url == url).one_or_none()
        if source is None:
            source = Source(url=url, url_hash=hashlib.sha256(url.encode()).hexdigest())
            self.db.add(source)
        source.raw_text = text
        source.summary = text[:1200]
        return source
