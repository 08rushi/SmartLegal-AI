# Auth & Persistence Setup Guide

## Files Changed / Created

### Backend (copy to your `backend/` folder)
| File | Action |
|------|--------|
| `auth_google.py` | **NEW** — Google OAuth endpoint |
| `main.py` | **UPDATED** — mounts Google OAuth router |

### Frontend (copy to matching paths in `frontend/src/`)
| File | Action | Destination |
|------|--------|-------------|
| `api.ts` | **UPDATED** — interceptors re-enabled + googleSignIn helper | `frontend/src/services/api.ts` |
| `authSlice.ts` | **UPDATED** — adds `loginWithGoogle` thunk | `frontend/src/store/authSlice.ts` |
| `Login.tsx` | **UPDATED** — fully wired form + Google button | `frontend/src/pages/Login.tsx` |
| `Register.tsx` | **UPDATED** — fully wired form + Google button | `frontend/src/pages/Register.tsx` |
| `MyDocuments.tsx` | **NEW** — document history page | `frontend/src/pages/MyDocuments.tsx` |
| `App.tsx` | **UPDATED** — adds /documents route | `frontend/src/App.tsx` |
| `Layout.tsx` | **UPDATED** — auth-aware navbar with user menu | `frontend/src/components/Layout.tsx` |
| `frontend_env_example` | **UPDATED** — adds VITE_GOOGLE_CLIENT_ID | `frontend/.env.example` |

---

## Step 1 — Copy the files

```bash
# From your project root (where this guide is)
cp auth_google.py backend/auth_google.py
cp main.py backend/main.py

cp api.ts frontend/src/services/api.ts
cp authSlice.ts frontend/src/store/authSlice.ts
cp Login.tsx frontend/src/pages/Login.tsx
cp Register.tsx frontend/src/pages/Register.tsx
cp MyDocuments.tsx frontend/src/pages/MyDocuments.tsx
cp App.tsx frontend/src/App.tsx
cp Layout.tsx frontend/src/components/Layout.tsx
```

---

## Step 2 — Install new backend dependency

```bash
cd backend
source venv/bin/activate    # or: venv\Scripts\activate on Windows
pip install httpx             # already in requirements.txt — verify it's there
```

---

## Step 3 — Google OAuth Setup (Optional but Recommended)

### Get your Google Client ID (free, 5 minutes):

1. Go to https://console.cloud.google.com/
2. Create a new project (or use existing)
3. Go to **APIs & Services → Credentials**
4. Click **+ Create Credentials → OAuth 2.0 Client ID**
5. Application type: **Web Application**
6. Add Authorized JavaScript origins:
   - `http://localhost:5173` (dev)
   - `https://your-app.vercel.app` (production)
7. Click **Create** → copy the **Client ID**

### Add to your .env files:

**`frontend/.env.local`** — add this line:
```
VITE_GOOGLE_CLIENT_ID=your_client_id_here.apps.googleusercontent.com
```

> If you leave `VITE_GOOGLE_CLIENT_ID` empty, Google Sign-In button shows as disabled
> and email/password login still works perfectly.

---

## Step 4 — Run & Test

```bash
# Terminal 1 — Backend
cd backend && uvicorn main:app --reload

# Terminal 2 — Frontend  
cd frontend && npm run dev
```

### Test checklist:
- [ ] Go to `/register` → fill form → submit → redirects to `/upload`
- [ ] Refresh page → still logged in (JWT persisted)
- [ ] Navbar shows your name + dropdown
- [ ] Click dropdown → "My Documents" link works
- [ ] `/documents` page shows upload history
- [ ] Click "Sign Out" → logged out, redirected to home
- [ ] Go to `/login` → sign in with same credentials → works
- [ ] (If Google Client ID set) Google button appears and works

---

## How JWT Persistence Works

```
User logs in
  ↓
Backend returns { access_token, user }
  ↓
authSlice stores token in:
  - Redux state (in-memory, lost on refresh)
  - localStorage key 'sl_token' (persists across refreshes)
  ↓
On every page load (App.tsx useEffect):
  if (localStorage.sl_token exists):
    dispatch(fetchCurrentUser())  → GET /api/v1/auth/me
    ↓
    Success: user restored to Redux state
    Failure (expired token): token cleared, user stays logged out
  ↓
api.ts request interceptor:
  Every API call automatically adds: Authorization: Bearer <token>
```

---

## What the My Documents Page Shows

- **Stats**: total docs, high risk clauses count, total clauses
- **Document list**: all uploads from Redux `document.history`
- **Per doc**: filename, type badge, size, upload date
- **Current doc** highlighted in gold
- **Actions**: View Analysis, Ask AI, Re-analyze
- **Risk summary** inline for the most recently analyzed doc
- **Upsell** for non-logged-in users to create account

> Note: `document.history` is currently in Redux (in-memory).
> After Phase 1B (backend hardening), it will be fetched from the DB.
> The DB already stores all documents with user_id — the `/documents` 
> history endpoint just needs to be built in `backend/routers/upload.py`.

---

## Next Steps (Phase 1B)

Once this is working, the next quick win is:

```python
# Add to backend/routers/upload.py:
@router.get("/history")
async def get_document_history(
    current_user=Depends(get_current_user),
    db=Depends(get_db),
):
    async with db.execute(
        "SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC",
        (current_user["id"],),
    ) as cur:
        docs = await cur.fetchall()
    return {"documents": [dict(d) for d in docs]}
```

This will make My Documents show all documents across sessions, not just the current browser session.
