# SmartLegal AI 🏛️

> **AI-Powered Legal Document Analyzer & Civic Service Guide for Indians**  
> Upload any contract (rental agreements, employment contracts, loan papers, NDAs) and receive plain-language explanations, clause-by-clause risk breakdowns, and risk warnings — in **English** and **Hindi**.

---

## ⚡ Quick Start

### 1. Backend Setup (FastAPI + Python 3.12)

```bash
cd backend
python -m venv venv
venv\Scripts\activate       # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt

# Create your .env configuration
cp .env.example .env
# Edit .env: set GROQ_API_KEY, DATABASE_URL and SECRET_KEY (>= 32 random chars,
# e.g. `openssl rand -hex 32`). GEMINI_API_KEY / OPENROUTER_API_KEY are optional fallbacks.

# Launch the FastAPI dev server
uvicorn main:app --reload --port 8000
```
- API Swagger Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/health

### 2. Frontend Setup (React 18 + Vite + Redux)

```bash
cd frontend
npm install

# Create your frontend environment configuration
cp .env.example .env.local

# Launch the Vite dev server
npm run dev
```
- Web Application: http://localhost:5173

---

## 🛠️ Tech Stack & Key Technologies

| Layer | Technology | Description |
|---|---|---|
| **Frontend** | React 18, TypeScript, Vite | Single Page Application with fast module reloading |
| **State Management** | Redux Toolkit | 10 slices (`auth`, `document`, `analysis`, `chat`, `advisor`, `insights`, `legalId`, `property`, `business`, `yojana`) |
| **Styling** | Custom Glassmorphic CSS + Tailwind | Custom dark theme with glowing risk indicators & dynamic micro-animations |
| **Backend API** | Python 3.12, FastAPI, Uvicorn | Async ASGI server with rate limiting & Sentry error tracing |
| **Database** | Supabase PostgreSQL + `asyncpg` (auto-fallback to local SQLite) | Relational store with connection pooling |
| **Cache / Jobs** | Redis (optional) + ARQ | L1 analysis cache and durable analysis worker; inline fallback without Redis |
| **AI LLM Engine** | Groq (default `openai/gpt-oss-120b`, set via `GROQ_MODEL`) → OpenRouter → Gemini | Primary provider with automatic fallback chain |
| **Extraction / OCR** | PyMuPDF; Gemini Vision → PaddleOCR → Tesseract for scans & images | PDFs and JPG/PNG/WebP up to 25 MB / 50 pages |
| **Security & Auth** | JWT (`python-jose`) + Google OAuth 2.0 | bcrypt password hashing + Google Identity Services integration |

---

## 📁 Repository Structure

```
smartlegal-ai/
├── README.md                           # Main Developer Guide & System Summary
├── AGENTS.md                           # AI Agent context & coding guidelines
├── CLAUDE.md                           # Claude context & guidelines
│
├── docs/                               # 📚 Centralized Documentation Suite
│   ├── CHANGELOG_AND_WORK_LOG.md       # Work Session History, Component Matrix & Code Changes Log
│   ├── ARCHITECTURE.md                 # Full System, Frontend, Backend & AI Pipeline Architecture
│   ├── DATABASE_ARCHITECTURE.md        # PostgreSQL (Supabase) Schema, ERD & Caching Topology
│   ├── AUTHENTICATION_AND_SECURITY.md  # JWT, bcrypt, Google OAuth 2.0 & Phase 4D Ownership Verification
│   ├── PROJECT_STATUS_AND_ROADMAP.md   # Current Milestone Status (Phase 1-4D) & Technical Roadmap
│   └── GOOGLE_OAUTH_SETUP.md           # Setup instructions for Google OAuth Client ID
│
├── frontend/                           # React 18 Frontend Application
│   └── src/
│       ├── components/                 # Shared UI (ClauseCard, RiskBadge, Layout, ProtectedRoute)
│       ├── pages/                      # Application Route Views
│       ├── store/                      # Redux Toolkit Store & Slices
│       ├── services/                   # Axios API Client & Google Sign-In helper
│       └── types/                      # TypeScript Interfaces & Definitions
│
└── backend/                            # FastAPI Backend Application
    ├── main.py                         # Application entrypoint, CORS & middleware
    ├── config.py                       # Pydantic Settings configuration from .env
    ├── database.py                     # Supabase PostgreSQL asyncpg connection pool
    ├── cache.py                        # Redis L1 caching module
    ├── routers/                        # API Endpoint Routers (auth, upload, analyze, chat, hubs)
    └── services/                       # AI LLM Services & Indian Legal Knowledge Bases
```

---

## 📚 Documentation Portal

For detailed technical guides, consult the [`docs/`](file:///c:/Core/SmartLegal-AI/docs) directory:

- 🧭 **[Work Log & Progress Matrix](file:///c:/Core/SmartLegal-AI/docs/CHANGELOG_AND_WORK_LOG.md)**: Session history, component states, and exact code diff logs.
- 🏗️ **[System Architecture](file:///c:/Core/SmartLegal-AI/docs/ARCHITECTURE.md)**: Deep dive into the frontend, FastAPI gateway, and LLM pipeline.
- 🗄️ **[Database Architecture](file:///c:/Core/SmartLegal-AI/docs/DATABASE_ARCHITECTURE.md)**: ER diagram, table schemas, and caching configuration.
- 🔒 **[Auth & Security Specifications](file:///c:/Core/SmartLegal-AI/docs/AUTHENTICATION_AND_SECURITY.md)**: JWT specifications, Google OAuth flow, and ownership verification.
- 🎯 **[Project Status & Roadmap](file:///c:/Core/SmartLegal-AI/docs/PROJECT_STATUS_AND_ROADMAP.md)**: Sprint completion stats, known issues, and roadmap.

---

## 📜 License & Disclaimers

SmartLegal AI provides automated legal document analysis and information based on Indian statutory laws. It does not constitute formal legal advice.
