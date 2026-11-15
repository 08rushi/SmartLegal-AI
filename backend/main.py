import os
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from PIL import Image

Image.MAX_IMAGE_PIXELS = 50_000_000  # decompression-bomb guard (default is ~179M)
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import get_settings
from database import init_db_pool, close_db_pool
from limiter import limiter
from cache import init_redis, close_redis
from routers import auth, upload, analyze, chat, advisor, insights, legal_id, property, business, yojana, whatsapp, internal_shadow, voice
import auth_google
from services.i18n_messages import translate_message
from services.lang import lang_from_request


settings = get_settings()



# ── Sentry ────────────────────────────────────────────────────────────────────
if settings.sentry_dsn:
    import sentry_sdk
    from sentry_sdk.integrations.fastapi import FastApiIntegration
    from sentry_sdk.integrations.starlette import StarletteIntegration

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        traces_sample_rate=1.0 if settings.sentry_environment == "development" else 0.1,
        send_default_pii=False,
        integrations=[
            StarletteIntegration(transaction_style="endpoint"),
            FastApiIntegration(transaction_style="endpoint"),
        ],
    )


# ── Background reaper: fail analyses orphaned by a worker restart ─────────────
async def _reaper_loop():
    import asyncio
    from database import get_db_ctx
    from routers.analyze import reap_stale_analyses

    interval = settings.analysis_reaper_interval_seconds
    while True:
        try:
            async with get_db_ctx() as db:
                await reap_stale_analyses(db)
        except Exception as exc:
            print(f"[reaper] loop error: {exc}")
        await asyncio.sleep(interval)


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio
    from database import get_db_ctx
    from routers.analyze import reap_stale_analyses

    # Startup
    await init_db_pool()
    await init_redis(settings.redis_url)   # no-op when REDIS_URL is blank

    # Sweep once on boot (catches jobs orphaned by the previous shutdown),
    # then run a periodic reaper in the background.
    try:
        async with get_db_ctx() as db:
            await reap_stale_analyses(db)
    except Exception as exc:
        print(f"[reaper] startup sweep failed: {exc}")
    reaper = asyncio.create_task(_reaper_loop())

    yield

    # Shutdown
    reaper.cancel()
    try:
        await reaper
    except (asyncio.CancelledError, Exception):
        pass
    await close_db_pool()
    await close_redis()


app = FastAPI(
    title="SmartLegal AI API",
    description="AI-powered legal document analysis for Indians",
    version="1.0.0",
    lifespan=lifespan,
)

# ── Rate limiter ──────────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# -- Localized errors: HTTPException.detail is translated using the X-Lang header --
@app.exception_handler(StarletteHTTPException)
async def _localized_http_exception_handler(request: Request, exc: StarletteHTTPException):
    detail = exc.detail
    if isinstance(detail, str):
        detail = translate_message(detail, lang_from_request(request))
    return JSONResponse(
        {"detail": detail},
        status_code=exc.status_code,
        headers=getattr(exc, "headers", None),
    )


async def _localized_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    lang = lang_from_request(request)
    response = JSONResponse(
        {
            "error": f"Rate limit exceeded: {exc.detail}",
            "detail": translate_message(f"Rate limit exceeded: {exc.detail}", lang),
        },
        status_code=429,
    )
    try:
        response = request.app.state.limiter._inject_headers(response, request.state.view_rate_limit)
    except Exception:
        pass
    return response


app.add_exception_handler(RateLimitExceeded, _localized_rate_limit_handler)

# ── CORS ──────────────────────────────────────────────────────────────────────
# In development accept the frontend on any localhost/127.0.0.1 port (Vite moves to
# 5174, 5175… when 5173 is busy, and browsers treat 127.0.0.1 as a different origin).
# Production uses only the explicit ALLOWED_ORIGINS list.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_origin_regex=None if settings.is_production else r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,         prefix="/api/v1/auth",      tags=["Auth"])
app.include_router(auth_google.router,  prefix="/api/v1/auth",      tags=["Auth"])
app.include_router(upload.router,       prefix="/api/v1/upload",    tags=["Upload"])
app.include_router(analyze.router,      prefix="/api/v1/analyze",   tags=["Analyze"])
app.include_router(chat.router,         prefix="/api/v1/chat",      tags=["Chat"])
app.include_router(advisor.router,      prefix="/api/v1/advisor",   tags=["Advisor"])
app.include_router(insights.router,     prefix="/api/v1/insights",  tags=["Insights"])
app.include_router(legal_id.router,     prefix="/api/v1/legal-id",  tags=["Legal ID"])
app.include_router(property.router,     prefix="/api/v1/property",  tags=["Property"])
app.include_router(business.router,     prefix="/api/v1/business",  tags=["Business"])
app.include_router(yojana.router,       prefix="/api/v1/yojana",    tags=["Jan-Yojana"])
app.include_router(voice.router,        prefix="/api/v1/voice",     tags=["Voice"])
# WhatsApp bot is a planned future integration: its code stays in the repo but is not
# mounted unless WHATSAPP_ENABLED=true (its dev endpoints are unauthenticated).
if settings.whatsapp_enabled:
    app.include_router(whatsapp.router, prefix="/api/v1/whatsapp", tags=["WhatsApp"])
app.include_router(internal_shadow.router,                          tags=["Internal Shadow"])
app.include_router(internal_shadow.router, prefix="/api/v1",         tags=["Internal Shadow"])



# Single-container deployment: when the built frontend is present (backend/static, copied in by the
# Dockerfile, or STATIC_DIR) this server also serves the website, so the browser talks to ONE origin
# (first-party cookie, no CORS, no custom domain needed).
STATIC_DIR = Path(os.environ.get("STATIC_DIR") or (Path(__file__).resolve().parent / "static"))
SERVE_FRONTEND = (STATIC_DIR / "index.html").is_file()

if not SERVE_FRONTEND:
    @app.get("/")
    async def root():
        return {"message": "SmartLegal AI API is running", "docs": "/docs"}


@app.get("/health")
async def health():
    from services.ocr_service import ocr_status
    return {"status": "ok", "ocr": ocr_status()}


# ── Frontend (single-page app) ────────────────────────────────────────────────
# Registered last so every API route above wins. Unknown non-API paths fall back to index.html.
if SERVE_FRONTEND:
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    if (STATIC_DIR / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    _NO_SPA_PREFIXES = ("api/", "internal/", "docs", "redoc", "openapi.json")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        if full_path.startswith(_NO_SPA_PREFIXES):
            raise StarletteHTTPException(status_code=404, detail="Not found")
        root_dir = STATIC_DIR.resolve()
        candidate = (STATIC_DIR / full_path).resolve()
        if full_path and candidate.is_file() and root_dir in candidate.parents:
            return FileResponse(candidate)
        return FileResponse(STATIC_DIR / "index.html", headers={"Cache-Control": "no-cache"})
