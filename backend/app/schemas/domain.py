from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class SearchRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    max_results: int = Field(default=10, ge=1, le=50)
    persist: bool = True


class CrawlRequest(BaseModel):
    urls: list[HttpUrl] = Field(min_length=1, max_length=20)
    render_js: bool = False


class IngestRequest(BaseModel):
    source_ids: list[int] | None = None
    urls: list[HttpUrl] | None = None
    collection_name: str = "wireless-knowledge"


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    collection_name: str = "wireless-knowledge"
    top_k: int = Field(default=6, ge=1, le=20)
    llm_provider: str | None = None


class SourceReference(BaseModel):
    url: str
    title: str | None = None
    confidence_score: float = 0.0
    chunk_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    confidence_score: float
    sources: list[SourceReference]


class CompanyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    website: str | None
    headquarters: str | None
    category: str | None
    confidence_score: int
    created_at: datetime


class ComponentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    component_type: str
    description: str | None


class TechnologyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    generation: str | None
    description: str | None


class ExpertiseRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    taxonomy_path: str | None
    description: str | None
