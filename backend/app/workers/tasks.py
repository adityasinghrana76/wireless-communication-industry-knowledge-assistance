from app.db.session import SessionLocal
from app.services.crawler import CrawlService
from app.services.vector_store import VectorStoreService
from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.ingest_url")
def ingest_url(url: str, collection_name: str = "wireless-knowledge") -> dict:
    db = SessionLocal()
    try:
        import asyncio

        sources = asyncio.run(CrawlService(db).crawl_urls([url]))
        chunks = VectorStoreService(db).ingest_sources(sources, collection_name)
        return {"url": url, "chunks": chunks}
    finally:
        db.close()
