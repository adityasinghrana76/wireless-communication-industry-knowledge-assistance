from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import create_access_token, require_role
from app.db.session import get_db
from app.models.domain import CompanyCategory
from app.models import Company, Component, Expertise, Source, Technology
from app.schemas import (
    ChatRequest,
    ChatResponse,
    CompanyRead,
    ComponentRead,
    CrawlRequest,
    ExpertiseRead,
    IngestRequest,
    SearchRequest,
    TechnologyRead,
)
from app.services.crawler import CrawlService
from app.services.extraction import ExtractionService
from app.services.rag import RagService
from app.services.search import SearchService
from app.services.vector_store import VectorStoreService

router = APIRouter()


@router.post("/auth/token")
def token(form: Annotated[OAuth2PasswordRequestForm, Depends()]):
    import secrets

    settings = get_settings()
    username_ok = secrets.compare_digest(form.username, settings.admin_username)
    password_ok = secrets.compare_digest(form.password, settings.admin_password)
    if not username_ok or not password_ok:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"access_token": create_access_token(form.username, role="admin"), "token_type": "bearer"}


@router.post("/search")
async def search(payload: SearchRequest, db: Annotated[Session, Depends(get_db)]):
    service = SearchService(db)
    results = await service.search(payload.query, payload.max_results)
    if payload.persist:
        service.persist_results(results)
    return {"query": payload.query, "results": results}


@router.post("/crawl", dependencies=[Depends(require_role("admin", "analyst"))])
async def crawl(payload: CrawlRequest, db: Annotated[Session, Depends(get_db)]):
    sources = await CrawlService(db).crawl_urls([str(url) for url in payload.urls], payload.render_js)
    return {"sources": [{"id": source.id, "url": source.url, "title": source.title} for source in sources]}


@router.post("/ingest", dependencies=[Depends(require_role("admin", "analyst"))])
async def ingest(payload: IngestRequest, db: Annotated[Session, Depends(get_db)]):
    query = db.query(Source)
    if payload.source_ids:
        query = query.filter(Source.id.in_(payload.source_ids))
    if payload.urls:
        query = query.filter(Source.url.in_([str(url) for url in payload.urls]))
    sources = query.all()
    extracted = _materialize_entities(db, sources)
    count = VectorStoreService(db).ingest_sources(sources, payload.collection_name)
    return {"chunks_ingested": count, "entities_extracted": extracted, "collection_name": payload.collection_name}


@router.post("/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest, db: Annotated[Session, Depends(get_db)]):
    return await RagService(VectorStoreService(db)).answer(
        payload.question, payload.collection_name, payload.top_k, payload.llm_provider
    )


@router.get("/companies", response_model=list[CompanyRead])
def companies(db: Annotated[Session, Depends(get_db)], limit: int = 50):
    return db.query(Company).order_by(Company.name).limit(limit).all()


@router.get("/components", response_model=list[ComponentRead])
def components(db: Annotated[Session, Depends(get_db)], limit: int = 50):
    return db.query(Component).order_by(Component.name).limit(limit).all()


@router.get("/technologies", response_model=list[TechnologyRead])
def technologies(db: Annotated[Session, Depends(get_db)], limit: int = 50):
    return db.query(Technology).order_by(Technology.name).limit(limit).all()


@router.get("/expertise", response_model=list[ExpertiseRead])
def expertise(db: Annotated[Session, Depends(get_db)], limit: int = 50):
    return db.query(Expertise).order_by(Expertise.name).limit(limit).all()


@router.get("/analytics")
def analytics(db: Annotated[Session, Depends(get_db)]):
    return {
        "total_companies": db.scalar(func.count(Company.id)),
        "total_components": db.scalar(func.count(Component.id)),
        "total_technologies": db.scalar(func.count(Technology.id)),
        "total_expertise": db.scalar(func.count(Expertise.id)),
        "latest_sources": [
            {"id": s.id, "url": s.url, "title": s.title, "retrieved_at": s.retrieved_at}
            for s in db.query(Source).order_by(Source.retrieved_at.desc()).limit(10)
        ],
        "ai_usage_metrics": {"chat_requests_24h": 0, "embedding_chunks_24h": 0},
    }


def _materialize_entities(db: Session, sources: list[Source]) -> dict[str, int]:
    extractor = ExtractionService()
    counts = {"companies": 0, "components": 0, "technologies": 0, "expertise": 0}
    for source in sources:
        text = source.raw_text or source.summary or ""
        entities = extractor.extract_entities(text)
        category = extractor.classify_company(text)
        for name in entities["companies"]:
            if db.query(Company).filter(Company.name == name).one_or_none() is None:
                db.add(Company(name=name, category=CompanyCategory(category), confidence_score=55))
                counts["companies"] += 1
        for name in entities["components"]:
            if db.query(Component).filter(Component.name == name).one_or_none() is None:
                db.add(Component(name=name, component_type=name.title()))
                counts["components"] += 1
        for name in entities["technologies"]:
            if db.query(Technology).filter(Technology.name == name).one_or_none() is None:
                generation = name if name in {"4G", "5G", "6G"} else None
                db.add(Technology(name=name, generation=generation))
                counts["technologies"] += 1
        for name in entities["expertise"]:
            if db.query(Expertise).filter(Expertise.name == name).one_or_none() is None:
                db.add(Expertise(name=name, taxonomy_path=f"Wireless/{name}"))
                counts["expertise"] += 1
    db.commit()
    return counts
