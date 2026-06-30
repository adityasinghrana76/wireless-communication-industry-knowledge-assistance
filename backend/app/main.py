import redis
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import text
from starlette.responses import JSONResponse

from app.api.routes import router
from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.chroma import get_chroma_client

settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit])

app = FastAPI(title=settings.app_name, version="0.1.0")
app.state.limiter = limiter

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(status_code=429, content={"detail": "Rate limit exceeded"})


@app.get("/health")
def health():
    return {"status": "ok", "environment": settings.environment}


@app.get("/ready")
def ready():
    checks = {
        "database": _check_database(),
        "redis": _check_redis(),
        "chromadb": _check_chromadb(),
    }
    healthy = all(check["status"] == "ok" for check in checks.values())
    status_code = 200 if healthy else 503
    return JSONResponse(
        status_code=status_code,
        content={"status": "ok" if healthy else "degraded", "checks": checks},
    )


def _check_database() -> dict[str, str]:
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - diagnostic endpoint
        return {"status": "error", "detail": exc.__class__.__name__}


def _check_redis() -> dict[str, str]:
    try:
        client = redis.Redis.from_url(settings.redis_url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - diagnostic endpoint
        return {"status": "error", "detail": exc.__class__.__name__}


def _check_chromadb() -> dict[str, str]:
    try:
        get_chroma_client().heartbeat()
        return {"status": "ok"}
    except Exception as exc:  # pragma: no cover - diagnostic endpoint
        return {"status": "error", "detail": exc.__class__.__name__}


app.include_router(router, prefix=settings.api_prefix)
