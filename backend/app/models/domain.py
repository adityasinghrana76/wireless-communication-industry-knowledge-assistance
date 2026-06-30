import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class CompanyCategory(str, enum.Enum):
    telecom_vendor = "Telecom Vendor"
    component_manufacturer = "Component Manufacturer"
    network_provider = "Network Provider"
    research_organization = "Research Organization"
    technology_company = "Technology Company"


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Company(Base, TimestampMixin):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    website: Mapped[str | None] = mapped_column(String(500))
    headquarters: Mapped[str | None] = mapped_column(String(255))
    category: Mapped[CompanyCategory | None] = mapped_column(Enum(CompanyCategory))
    confidence_score: Mapped[int] = mapped_column(Integer, default=0)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    products: Mapped[list["Product"]] = relationship(back_populates="company")
    sources: Mapped[list["Source"]] = relationship(back_populates="company")


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (UniqueConstraint("company_id", "name", name="uq_product_company_name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"))
    name: Mapped[str] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)

    company: Mapped[Company | None] = relationship(back_populates="products")
    components: Mapped[list["Component"]] = relationship(secondary="product_components")
    technologies: Mapped[list["Technology"]] = relationship(secondary="product_technologies")


class Component(Base, TimestampMixin):
    __tablename__ = "components"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    component_type: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str | None] = mapped_column(Text)


class Technology(Base, TimestampMixin):
    __tablename__ = "technologies"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    generation: Mapped[str | None] = mapped_column(String(40), index=True)
    description: Mapped[str | None] = mapped_column(Text)


class Expertise(Base, TimestampMixin):
    __tablename__ = "expertise"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    taxonomy_path: Mapped[str | None] = mapped_column(String(500), index=True)
    description: Mapped[str | None] = mapped_column(Text)


class Source(Base, TimestampMixin):
    __tablename__ = "sources"
    __table_args__ = (Index("ix_sources_url_hash", "url_hash"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id", ondelete="SET NULL"))
    url: Mapped[str] = mapped_column(String(1000), unique=True)
    url_hash: Mapped[str] = mapped_column(String(64))
    title: Mapped[str | None] = mapped_column(String(500))
    raw_text: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    retrieved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    credibility_score: Mapped[int] = mapped_column(Integer, default=50)

    company: Mapped[Company | None] = relationship(back_populates="sources")
    documents: Mapped[list["ResearchDocument"]] = relationship(back_populates="source")


class ResearchDocument(Base, TimestampMixin):
    __tablename__ = "research_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(500))
    abstract: Mapped[str | None] = mapped_column(Text)
    publication_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    authors: Mapped[list] = mapped_column(JSONB, default=list)

    source: Mapped[Source] = relationship(back_populates="documents")


class EmbeddingMetadata(Base, TimestampMixin):
    __tablename__ = "embeddings_metadata"
    __table_args__ = (Index("ix_embedding_collection_doc", "collection_name", "document_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    collection_name: Mapped[str] = mapped_column(String(120), index=True)
    document_id: Mapped[str] = mapped_column(String(160), unique=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    chunk_text: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)


class ProductComponent(Base):
    __tablename__ = "product_components"
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    component_id: Mapped[int] = mapped_column(ForeignKey("components.id", ondelete="CASCADE"), primary_key=True)


class ProductTechnology(Base):
    __tablename__ = "product_technologies"
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), primary_key=True)
    technology_id: Mapped[int] = mapped_column(ForeignKey("technologies.id", ondelete="CASCADE"), primary_key=True)
