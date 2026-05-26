from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from config import get_settings
from database import init_db
from limiter import limiter
from cache import init_redis, close_redis
from routers import auth, upload, analyze, chat
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


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    await init_redis(settings.redis_url)   # no-op when REDIS_URL is blank
    yield
    # Shutdown
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
app.include_router(auth.router,         prefix="/api/v1/auth",    tags=["Auth"])
app.include_router(auth_google.router,  prefix="/api/v1/auth",    tags=["Auth"])
app.include_router(upload.router,       prefix="/api/v1/upload",  tags=["Upload"])
app.include_router(analyze.router,      prefix="/api/v1/analyze", tags=["Analyze"])
app.include_router(chat.router,         prefix="/api/v1/chat",    tags=["Chat"])


@app.get("/")
async def root():
    return {"message": "SmartLegal AI API is running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}