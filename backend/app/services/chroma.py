from functools import lru_cache

import chromadb
from chromadb.config import Settings

from app.core.config import get_settings


@lru_cache
def get_chroma_client():
    settings = get_settings()
    return chromadb.HttpClient(
        host=settings.chroma_host,
        port=settings.chroma_port,
        settings=Settings(anonymized_telemetry=False),
    )
