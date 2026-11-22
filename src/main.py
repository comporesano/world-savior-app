"""Точка входа: сборка FastAPI-приложения, статика SPA, обработчики ошибок."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.extension import _rate_limit_exceeded_handler

from .config import settings
from .db import Base, engine
from .errors import register_error_handlers
from .limiter import limiter
from .routers import auth, events, me, misc, users


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version=settings.version, lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

register_error_handlers(app)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    # Для /docs Swagger UI грузит ресурсы с CDN, поэтому CSP там не ставим
    if not request.url.path.startswith("/docs"):
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'self'; form-action 'self'")
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(me.router, prefix="/api/v1/me", tags=["me"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(events.router, prefix="/api/v1/events", tags=["events"])
app.include_router(misc.router, prefix="/api/v1", tags=["misc"])


@app.get("/api/v1/health", tags=["system"])
def health():
    return {"status": "ok"}


# SPA: статика + index.html на корне (клиентский роутинг — на хешах, fallback не нужен)
app.mount("/static", StaticFiles(directory=settings.static_dir), name="static")


@app.get("/", include_in_schema=False)
def index():
    return FileResponse(settings.static_dir / "index.html")
