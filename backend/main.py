from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import get_settings
from database import init_db_pool, close_db_pool
from limiter import limiter
from cache import init_redis, close_redis
from routers import auth, upload, analyze, chat, advisor, insights, legal_id, property, business, yojana
import auth_google

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

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
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



@app.get("/")
async def root():
    return {"message": "SmartLegal AI API is running", "docs": "/docs"}


@app.get("/health")
async def health():
    from services.ocr_service import ocr_status
    return {"status": "ok", "ocr": ocr_status()}