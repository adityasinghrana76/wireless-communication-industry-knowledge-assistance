import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.models import EmbeddingMetadata, Source
from app.services.chroma import get_chroma_client


class VectorStoreService:
    def __init__(self, db: Session):
        self.db = db
        self.client = get_chroma_client()
        self.splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=160)

    def ingest_sources(self, sources: list[Source], collection_name: str) -> int:
        collection = self.client.get_or_create_collection(collection_name)
        count = 0
        for source in sources:
            chunks = self.splitter.split_text(source.raw_text or source.summary or "")
            ids, docs, metas = [], [], []
            for index, chunk in enumerate(chunks):
                doc_id = f"src-{source.id}-{uuid.uuid4().hex[:12]}"
                ids.append(doc_id)
                docs.append(chunk)
                metas.append({"source_id": source.id, "url": source.url, "title": source.title or ""})
                self.db.add(
                    EmbeddingMetadata(
                        source_id=source.id,
                        collection_name=collection_name,
                        document_id=doc_id,
                        chunk_index=index,
                        chunk_text=chunk,
                        metadata_json=metas[-1],
                    )
                )
            if ids:
                collection.add(ids=ids, documents=docs, metadatas=metas)
                count += len(ids)
        self.db.commit()
        return count

    def query(self, collection_name: str, question: str, top_k: int) -> list[dict]:
        has_embeddings = (
            self.db.query(EmbeddingMetadata.id)
            .filter(EmbeddingMetadata.collection_name == collection_name)
            .first()
            is not None
        )
        if not has_embeddings:
            return []

        collection = self.client.get_or_create_collection(collection_name)
        result = collection.query(query_texts=[question], n_results=top_k)
        docs = result.get("documents", [[]])[0]
        metas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            {"text": doc, "metadata": meta, "score": max(0.0, 1.0 - float(distance))}
            for doc, meta, distance in zip(docs, metas, distances, strict=False)
        ]
