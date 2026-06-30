CREATE TYPE company_category AS ENUM (
  'Telecom Vendor',
  'Component Manufacturer',
  'Network Provider',
  'Research Organization',
  'Technology Company'
);

CREATE TABLE companies (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  website VARCHAR(500),
  headquarters VARCHAR(255),
  category company_category,
  confidence_score INTEGER NOT NULL DEFAULT 0,
  metadata_json JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_companies_name ON companies (name);

CREATE TABLE products (
  id BIGSERIAL PRIMARY KEY,
  company_id BIGINT REFERENCES companies(id) ON DELETE SET NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_product_company_name UNIQUE (company_id, name)
);
CREATE INDEX ix_products_name ON products (name);

CREATE TABLE components (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  component_type VARCHAR(120) NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_components_name ON components (name);
CREATE INDEX ix_components_component_type ON components (component_type);

CREATE TABLE technologies (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL UNIQUE,
  generation VARCHAR(40),
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_technologies_name ON technologies (name);
CREATE INDEX ix_technologies_generation ON technologies (generation);

CREATE TABLE expertise (
  id BIGSERIAL PRIMARY KEY,
  name VARCHAR(160) NOT NULL UNIQUE,
  taxonomy_path VARCHAR(500),
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_expertise_name ON expertise (name);
CREATE INDEX ix_expertise_taxonomy_path ON expertise (taxonomy_path);

CREATE TABLE sources (
  id BIGSERIAL PRIMARY KEY,
  company_id BIGINT REFERENCES companies(id) ON DELETE SET NULL,
  url VARCHAR(1000) NOT NULL UNIQUE,
  url_hash VARCHAR(64) NOT NULL,
  title VARCHAR(500),
  raw_text TEXT,
  summary TEXT,
  retrieved_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  credibility_score INTEGER NOT NULL DEFAULT 50,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_sources_url_hash ON sources (url_hash);

CREATE TABLE research_documents (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  title VARCHAR(500) NOT NULL,
  abstract TEXT,
  publication_date TIMESTAMPTZ,
  authors JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_research_documents_source_id ON research_documents (source_id);

CREATE TABLE embeddings_metadata (
  id BIGSERIAL PRIMARY KEY,
  source_id BIGINT NOT NULL REFERENCES sources(id) ON DELETE CASCADE,
  collection_name VARCHAR(120) NOT NULL,
  document_id VARCHAR(160) NOT NULL UNIQUE,
  chunk_index INTEGER NOT NULL,
  chunk_text TEXT NOT NULL,
  metadata_json JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_embeddings_metadata_source_id ON embeddings_metadata (source_id);
CREATE INDEX ix_embedding_collection_doc ON embeddings_metadata (collection_name, document_id);

CREATE TABLE product_components (
  product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  component_id BIGINT NOT NULL REFERENCES components(id) ON DELETE CASCADE,
  PRIMARY KEY (product_id, component_id)
);

CREATE TABLE product_technologies (
  product_id BIGINT NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  technology_id BIGINT NOT NULL REFERENCES technologies(id) ON DELETE CASCADE,
  PRIMARY KEY (product_id, technology_id)
);
