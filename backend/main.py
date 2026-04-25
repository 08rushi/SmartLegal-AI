from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from config import get_settings
from database import init_db
from routers import auth, upload, analyze, chat

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables
    await init_db()
    yield
    # Shutdown: nothing needed


app = FastAPI(
    title="SmartLegal AI API",
    description="AI-powered legal document analysis for Indians",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers under /api/v1
app.include_router(auth.router,    prefix="/api/v1/auth",    tags=["Auth"])
app.include_router(upload.router,  prefix="/api/v1/upload",  tags=["Upload"])
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["Analyze"])
app.include_router(chat.router,    prefix="/api/v1/chat",    tags=["Chat"])


@app.get("/")
async def root():
    return {"message": "SmartLegal AI API is running", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
