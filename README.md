# Wireless Communication Industry Knowledge Assistance

Production-shaped AI platform scaffold for wireless communication market intelligence. It includes FastAPI, React, PostgreSQL, ChromaDB, Redis, Celery, internet search/crawling hooks, RAG chat, deployment manifests.

## Quick Start

```bash
cp .env.example .env
docker compose up --build
```

Services:

- Frontend: http://localhost:5173
- Backend: http://localhost:18000
- API docs: http://localhost:18000/docs
- ChromaDB: http://localhost:18001

The host ports can be overridden with `FRONTEND_HOST_PORT`, `BACKEND_HOST_PORT`, `CHROMA_HOST_PORT`, `REDIS_HOST_PORT`, and `POSTGRES_HOST_PORT`.

Set `OPENAI_API_KEY` and optionally `TAVILY_API_KEY` in your shell or `.env` before starting for live LLM answers and internet search.

Useful operational checks:

```bash
curl http://localhost:18000/health
curl http://localhost:18000/ready
docker compose ps
docker compose logs -f backend
```

For a real deployment, replace `JWT_SECRET`, `ADMIN_PASSWORD`, and `POSTGRES_PASSWORD` in `.env` with strong secret values. Keep `.env` out of git.

## Core Artifacts

- Backend API: [backend/app/main.py](/home/adityarana/wireless-communication-industry-knowledge-assistance/backend/app/main.py)
- Database schema: [backend/schema.sql](/home/adityarana/wireless-communication-industry-knowledge-assistance/backend/schema.sql)
- Frontend dashboard: [frontend/src/main.tsx](/home/adityarana/wireless-communication-industry-knowledge-assistance/frontend/src/main.tsx)
- Architecture: [docs/architecture.md](/home/adityarana/wireless-communication-industry-knowledge-assistance/docs/architecture.md)
- Docker Compose: [docker-compose.yml](/home/adityarana/wireless-communication-industry-knowledge-assistance/docker-compose.yml)
- Kubernetes: [infra/k8s](/home/adityarana/wireless-communication-industry-knowledge-assistance/infra/k8s)
- Helm chart: [infra/helm/wireless-intel](/home/adityarana/wireless-communication-industry-knowledge-assistance/infra/helm/wireless-intel)

## Implemented APIs

- `POST /api/v1/search`
- `POST /api/v1/crawl`
- `POST /api/v1/ingest`
- `POST /api/v1/chat`
- `GET /api/v1/companies`
- `GET /api/v1/components`
- `GET /api/v1/technologies`
- `GET /api/v1/expertise`
- `GET /api/v1/analytics`
- `GET /health`
- `GET /ready`

## Real-World Readiness

This project now includes production-oriented foundations:

- Container healthchecks for PostgreSQL, Redis, ChromaDB, backend, and frontend.
- Backend readiness endpoint that verifies database, Redis, and ChromaDB connectivity.
- Environment-driven secrets and host ports.
- Backend and worker containers running as a non-root user.
- Pinned ChromaDB Python client/server versions to avoid API drift.

