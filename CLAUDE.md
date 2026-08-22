# SmartLegal AI — Claude Guidelines & Project Context

## What this project is
AI-powered legal document analyzer & civic service platform tailored for Indian citizens. Users upload rental agreements, employment contracts, loan papers, NDAs, or commercial leases → get plain-language explanations, risk warnings, and clause-by-clause breakdown in **English** and **Hindi**, along with guided application workflows for Indian IDs, Property services, and Business licenses.

## Current Status
- ✅ **Phase 1 (Scaffold)**: FastAPI backend + Vite React 18 + Redux Toolkit + Supabase PostgreSQL schema.
- ✅ **Phase 2 (UI Components)**: Upload drag & drop, Analysis cockpit with Hindi translation toggle, Risk Badges, Q&A Chat, Document Compare placeholder, Service Tracker, and Civic Hubs.
- ✅ **Phase 3 (AI Pipeline)**: PyMuPDF text extraction + Groq / Gemini LLM prompt pipeline with JSON structured outputs & Indian Law Knowledge Bases.
- ✅ **Phase 4A-4D (Auth & Security)**: JWT Auth + Google OAuth 2.0 + Redux Auth integration + 100% Backend & Frontend ownership verification on all 24 protected routes.
- 🔄 **Work Log & Documentation Suite**: Unified documentation portal established under `docs/` with work session logging in `docs/CHANGELOG_AND_WORK_LOG.md`.

## Key Technical Decisions
- **Backend**: Python 3.12 + FastAPI + `asyncpg` (Supabase PostgreSQL pool) + `redis.asyncio` (L1 Cache) + Groq (`llama-3.3-70b`) & Gemini (`gemini-2.0-flash`) dual LLM pipeline.
- **Frontend**: React 18 + TypeScript + Vite + Redux Toolkit (7 slices) + Custom Glassmorphic Dark Theme + React Router v6 (`ProtectedRoute`).
- **Auth**: JWT Bearer token stored in `localStorage` (`sl_token`), Google Identity Services ID token verification, bcrypt password hashing.

## Key Documentation References
- Work Log & Component Matrix: [`docs/CHANGELOG_AND_WORK_LOG.md`](file:///c:/Core/SmartLegal-AI/docs/CHANGELOG_AND_WORK_LOG.md)
- System Architecture: [`docs/ARCHITECTURE.md`](file:///c:/Core/SmartLegal-AI/docs/ARCHITECTURE.md)
- Database Architecture & Schema: [`docs/DATABASE_ARCHITECTURE.md`](file:///c:/Core/SmartLegal-AI/docs/DATABASE_ARCHITECTURE.md)
- Auth & Security Specifications: [`docs/AUTHENTICATION_AND_SECURITY.md`](file:///c:/Core/SmartLegal-AI/docs/AUTHENTICATION_AND_SECURITY.md)
- Project Status & Roadmap: [`docs/PROJECT_STATUS_AND_ROADMAP.md`](file:///c:/Core/SmartLegal-AI/docs/PROJECT_STATUS_AND_ROADMAP.md)

## How to Run

### Backend
```bash
cd backend
venv\Scripts\activate          # Linux/macOS: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
# Runs on http://localhost:8000 (Swagger docs at http://localhost:8000/docs)
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```