# SmartLegal AI — Project Context for Claude

## What this project is
AI-powered legal document analyzer for Indians. Users upload rental agreements, employment contracts, loan papers → get plain-language explanations, risk warnings, and clause-by-clause breakdown in English and Hindi.

## Current Status
- ✅ Step 1: Project scaffold complete (folder structure, configs, Redux store, FastAPI backend)
- ✅ Step 2: UI pages built (Upload, Analysis, Chat, Layout, Login, Register, Compare)
- 🔄 Step 3: In progress — fixing upload flow, then adding auth

## Known Issues to Fix
- Windows `/tmp/` path issue in `backend/routers/upload.py` — use `tempfile.gettempdir()` instead
- Auth temporarily disabled for testing (upload/analyze routes use "anonymous" user_id)
- PyMuPDF may not be installed — `pip install PyMuPDF` in venv

## Tech Stack
### Frontend
- React 18 + TypeScript + Vite
- Redux Toolkit (4 slices: auth, document, analysis, chat)
- Tailwind CSS
- React Router v6
- Axios (api client in src/services/api.ts)
- React Dropzone (file upload)

### Backend
- Python 3.12 + FastAPI + uvicorn
- Google Gemini 2.5 Flash (gemini-2.0-flash model)
- PyMuPDF for PDF text extraction
- aiosqlite + SQLite database
- JWT auth (python-jose + passlib)

## Folder Structure
```
smartlegal-ai/
├── frontend/
│   └── src/
│       ├── store/
│       │   ├── index.ts
│       │   ├── authSlice.ts       # JWT login/register/me
│       │   ├── documentSlice.ts   # upload, progress, history
│       │   ├── analysisSlice.ts   # Gemini AI results, risk scores
│       │   └── chatSlice.ts       # Q&A conversation history
│       ├── pages/
│       │   ├── Home.tsx
│       │   ├── Upload.tsx         # Drag & drop with progress bar
│       │   ├── Analysis.tsx       # Clause cards + risk badges
│       │   ├── Chat.tsx           # Q&A chat on document
│       │   ├── Compare.tsx        # Side-by-side comparison (TODO)
│       │   ├── Login.tsx
│       │   ├── Register.tsx
│       │   └── Layout.tsx         # Navbar + footer wrapper
│       ├── components/
│       │   ├── ClauseCard.tsx     # Single clause with risk + Hindi toggle
│       │   └── RiskBadge.tsx      # Red/yellow/green risk indicator
│       ├── services/
│       │   └── api.ts             # Axios client (auth interceptors disabled for now)
│       ├── hooks/
│       │   └── redux.ts           # useAppDispatch, useAppSelector
│       └── types/
│           └── index.ts           # All TypeScript interfaces
│
└── backend/
    ├── main.py                    # FastAPI app + CORS + router mounts
    ├── database.py                # SQLite init + get_db dependency
    ├── config.py                  # pydantic-settings from .env
    ├── routers/
    │   ├── auth.py                # POST /auth/login, /auth/register, GET /auth/me
    │   ├── upload.py              # POST /upload (auth disabled for testing)
    │   ├── analyze.py             # POST /analyze (auth disabled for testing)
    │   └── chat.py                # POST /chat, GET /chat/{doc_id}/history
    └── services/
        ├── gemini_service.py      # analyze_legal_document() + answer_question_about_document()
        └── pdf_parser.py          # extract_text_from_pdf() using PyMuPDF

```

## API Endpoints
```
POST /api/v1/auth/register     { name, email, password }
POST /api/v1/auth/login        form-data: username, password
GET  /api/v1/auth/me           Bearer token required

POST /api/v1/upload            multipart/form-data: file
POST /api/v1/analyze           { document_id }
POST /api/v1/chat              { document_id, question }
GET  /api/v1/chat/{doc_id}/history
```

## Redux Slices Summary
```typescript
// documentSlice
state.document.current          // UploadedDocument | null
state.document.status           // 'idle' | 'uploading' | 'processing' | 'ready' | 'error'
state.document.uploadProgress   // 0-100

// analysisSlice
state.analysis.result           // AnalysisResult | null (has summary + clauses[])
state.analysis.isLoading        // boolean

// chatSlice
state.chat.messages             // ChatMessage[]
state.chat.isLoading            // boolean

// authSlice
state.auth.user                 // User | null
state.auth.token                // string | null (also in localStorage as 'sl_token')
```

## Key Type Definitions (src/types/index.ts)
```typescript
type RiskLevel = 'low' | 'medium' | 'high'

interface Clause {
  id, title, original_text, plain_english, plain_hindi,
  risk_level, risk_score (1-10), risk_reason, clause_type
}

interface DocumentSummary {
  document_type, parties[], key_dates[],
  overall_risk, risk_summary,
  total_clauses, high_risk_count, medium_risk_count, low_risk_count
}
```

## Environment Variables

### backend/.env
```
GEMINI_API_KEY=           # from aistudio.google.com (FREE)
SECRET_KEY=               # run: python -c "import secrets; print(secrets.token_hex(32))"
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080
DATABASE_URL=sqlite:///./smartlegal.db
ALLOWED_ORIGINS=http://localhost:5173
```

### frontend/.env.local
```
VITE_API_BASE_URL=http://localhost:8000
```

## How to Run

### Backend
```bash
cd backend
venv\Scripts\activate          # Windows
pip install -r requirements.txt
pip install PyMuPDF email-validator
uvicorn main:app --reload
# Runs on http://localhost:8000
# Swagger docs at http://localhost:8000/docs
```

### Frontend
```bash
cd frontend
npm install
npm run dev
# Runs on http://localhost:5173
```

## What's Next (Step 3)
- [ ] Fix Windows /tmp/ path in upload.py (use tempfile.gettempdir())
- [ ] Install PyMuPDF: pip install PyMuPDF
- [ ] Wire Login/Register pages to Redux authSlice
- [ ] Re-enable JWT auth on upload/analyze/chat routes
- [ ] Add protected route wrapper component
- [ ] Build Compare page (2 docs side by side)
- [ ] Document history page
- [ ] Deploy: Vercel (frontend) + Render.com (backend)

## Common Errors & Fixes
| Error                               | Fix                                             |
|-------------------------------------|-------------------------------------------------|
| `No module named 'email_validator'` | `pip install email-validator`                   |
| `PyMuPDF` build fails               | Use Python 3.12, not 3.14                       |
| `source venv/bin/activate` fails    | Windows: use `venv\Scripts\activate`            |
| `/tmp/` path error on Windows       | Use `tempfile.gettempdir()`                     |
| 401 Unauthorized on upload          | Auth interceptor in api.ts needs to be disabled |
| PostCSS `export default` error      | Use `module.exports =` in postcss.config.js     |

## Interview Talking Points
- Redux Toolkit with 4 slices showing real separation of concerns
- Async thunks for all API calls with proper loading/error states
- Gemini Vision API for document understanding (RAG-style Q&A)
- FastAPI with auto-generated Swagger docs
- JWT auth with bcrypt password hashing
- India-specific: Hindi translations, India legal context in prompts