# SmartLegal AI 🏛️

> AI-powered legal document analyzer for Indians. Upload any contract, get plain-language explanations, risk warnings, and clause-by-clause breakdown — in English and Hindi.

## Quick Start

### 1. Backend setup

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Start the server
uvicorn main:app --reload --port 8000
```

Visit http://localhost:8000/docs to see the auto-generated API docs.

### 2. Frontend setup

```bash
cd frontend
npm install

# Create your .env file
cp .env.example .env.local

# Start the dev server
npm run dev
```

Visit http://localhost:5173

---

## Get your free Gemini API key

1. Go to https://aistudio.google.com
2. Click "Get API key" → "Create API key"
3. Paste into `backend/.env` as `GEMINI_API_KEY=...`

No credit card required. Free tier is enough for portfolio use.

---

## Project Structure

```
smartlegal-ai/
├── frontend/                    # React + Redux + TypeScript
│   └── src/
│       ├── store/               # Redux slices
│       │   ├── authSlice.ts
│       │   ├── documentSlice.ts
│       │   ├── analysisSlice.ts
│       │   └── chatSlice.ts
│       ├── pages/               # Route components
│       │   ├── Home.tsx
│       │   ├── Upload.tsx
│       │   ├── Analysis.tsx
│       │   ├── Chat.tsx
│       │   └── Compare.tsx
│       ├── components/          # Shared UI components
│       ├── services/api.ts      # Axios client
│       └── types/index.ts       # All TypeScript types
│
└── backend/                     # Python + FastAPI
    ├── main.py                  # App entry + CORS
    ├── database.py              # SQLite setup
    ├── config.py                # Settings from .env
    ├── routers/
    │   ├── auth.py              # Login / register
    │   ├── upload.py            # PDF upload
    │   ├── analyze.py           # Gemini AI analysis
    │   └── chat.py              # Q&A chat
    └── services/
        ├── gemini_service.py    # All Gemini AI calls
        └── pdf_parser.py        # PyMuPDF text extraction
```

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 18, Redux Toolkit, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, aiosqlite |
| AI | Google Gemini 2.5 Flash (free) |
| PDF | PyMuPDF |
| Auth | JWT (python-jose + passlib) |
| Deployment | Vercel + Render.com (₹0) |

## Deployment (Free)

- **Frontend** → [Vercel](https://vercel.com) — connect GitHub repo, auto-deploys
- **Backend** → [Render.com](https://render.com) — create Web Service, set env vars
- **DB** → SQLite on Render (or upgrade to Supabase free tier)
- **Files** → [Cloudinary](https://cloudinary.com) free tier
