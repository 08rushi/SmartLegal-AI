# Phase 4D: Access Control & Ownership Verification - Implementation Guide

**Objective:** Ensure users can only access their own documents and analysis results.  
**Status:** READY TO IMPLEMENT  
**Estimated Effort:** 2-3 days  
**Priority:** P0 - CRITICAL for privacy/security

---

## Routes Requiring Ownership Checks

### Group 1: Document Analysis & Chat (CRITICAL)

#### analyze.py - 3 routes
1. **`POST /api/v1/analyze`** (currently public)
   - **Current:** Anyone can analyze any document by document_id
   - **Fix:** Add ownership check - only owner of document_id can analyze
   - **Code:** `if doc['user_id'] != current_user['id']: raise 403`

2. **`GET /api/v1/analyze/{document_id}/status`** (currently public)
   - **Current:** Anyone can check analysis status
   - **Fix:** Add ownership check
   - **Code:** Same pattern as above

3. **`DELETE /api/v1/analyze/{document_id}/cache`** (currently public)
   - **Current:** Anyone can delete cached analysis
   - **Fix:** Add ownership check
   - **Code:** Same pattern as above

#### chat.py - 2 routes
4. **`POST /api/v1/chat`** (currently public)
   - **Current:** Anyone can chat on any document
   - **Fix:** Add ownership check before processing question
   - **Code:** Verify document_id owner matches current_user

5. **`GET /api/v1/chat/{document_id}/history`** (currently public)
   - **Current:** Anyone can read chat history
   - **Fix:** Add ownership check
   - **Code:** Only return messages for owned documents

#### upload.py - 1 route
6. **`GET /api/v1/upload/{document_id}`** (currently public)
   - **Current:** Anyone can fetch any document metadata
   - **Fix:** Add ownership check (with admin bypass option)
   - **Code:** Verify document_id owner

### Group 2: New Hubs (4D Additions)

These are the new hub routes that need ownership from the start:

#### legal_id.py - 6 routes
7. **`POST /api/v1/legal-id/applications`** - Ownership: current_user creates
8. **`GET /api/v1/legal-id/applications`** - Filter to current_user only
9. **`GET /api/v1/legal-id/applications/{app_id}`** - Verify ownership
10. **`PATCH /api/v1/legal-id/applications/{app_id}`** - Verify ownership
11. **`DELETE /api/v1/legal-id/applications/{app_id}`** - Verify ownership
12. **`GET /api/v1/legal-id/applications/{app_id}/checklist`** - Verify ownership

#### property.py - 6 routes
13-18. **Same pattern as legal_id.py**

#### business.py - 6 routes
19-24. **Same pattern as legal_id.py**

---

## Implementation Steps

### Step 1: Update analyze.py Routes

**File:** `backend/routers/analyze.py`

**Current Code Pattern:**
```python
@router.post("")
async def analyze(data: AnalyzeRequest, db=Depends(get_db)):
    # Fetch document (NO OWNERSHIP CHECK)
    doc = await get_document(data.document_id, db)
```

**New Code Pattern:**
```python
from routers.auth import get_current_user  # Import at top

@router.post("")
async def analyze(
    data: AnalyzeRequest, 
    current_user=Depends(get_current_user),  # Add dependency
    db=Depends(get_db)
):
    # Fetch document
    async with db.execute(
        "SELECT * FROM documents WHERE id = ? AND user_id = ?",
        (data.document_id, current_user['id'])
    ) as cur:
        doc = await cur.fetchone()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Continue with analysis logic...
```

**Changes Needed:**
1. Add `current_user=Depends(get_current_user)` parameter to all routes
2. Update document queries to include `AND user_id = ?` condition
3. Raise 404 if document not found or not owned (don't distinguish - privacy)
4. Apply to:
   - `POST /api/v1/analyze` 
   - `GET /api/v1/analyze/{document_id}/status`
   - `DELETE /api/v1/analyze/{document_id}/cache`

### Step 2: Update chat.py Routes

**File:** `backend/routers/chat.py`

**Changes:**
1. Add `current_user=Depends(get_current_user)` to both routes
2. Verify document belongs to current_user before processing
3. When retrieving history, filter to current_user's messages
4. Apply to:
   - `POST /api/v1/chat`
   - `GET /api/v1/chat/{document_id}/history`

**Code Pattern:**
```python
@router.post("")
async def chat(
    data: ChatRequest,
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    # Verify document ownership
    async with db.execute(
        "SELECT id FROM documents WHERE id = ? AND user_id = ?",
        (data.document_id, current_user['id'])
    ) as cur:
        if not await cur.fetchone():
            raise HTTPException(status_code=403, detail="Access denied")
    
    # Continue with chat logic...
```

### Step 3: Update upload.py Routes

**File:** `backend/routers/upload.py`

**Changes:**
1. Add auth check to `GET /api/v1/upload/{document_id}`
2. When uploading, associate with current_user (already done if auth enabled)
3. Filter history to current_user only

**Current Issue:**
- Upload route currently uses "anonymous" if no JWT
- Need to decide: Require auth or allow anonymous?

### Step 4: Update New Hub Routes (legal_id, property, business)

**Files:** `backend/routers/legal_id.py`, `property.py`, `business.py`

These should already have ownership checks since they're new, but verify:

1. POST endpoints should set `user_id = current_user['id']`
2. GET endpoints should filter `WHERE user_id = ?`
3. PATCH/DELETE endpoints should verify ownership

**Code Template for all hub routes:**
```python
@router.get("/applications", response_model=dict)
async def list_applications(
    current_user=Depends(get_current_user),
    db=Depends(get_db)
):
    async with db.execute(
        "SELECT * FROM id_applications WHERE user_id = ? ORDER BY created_at DESC",
        (current_user['id'],)
    ) as cur:
        apps = await cur.fetchall()
    # Return applications list
```

---

## Testing Strategy

### Unit Tests
1. **Test: User A cannot access User B's document**
   ```python
   # Create user A, B
   # User A creates document
   # User B tries to access → 403 or 404
   ```

2. **Test: Own documents are accessible**
   ```python
   # User A creates document
   # User A analyzes → success
   # User A chats → success
   ```

3. **Test: 401 without token**
   ```python
   # Try analyze without Authorization header → 401
   ```

### Integration Tests
1. Register → Login → Upload → Analyze → Chat
2. Cross-user access attempt (should fail)
3. Token expiry (after 7 days, should fail)

### Manual Testing
1. Open browser, register as User A
2. Upload document → analyze → chat
3. Open incognito, register as User B
4. Try to access User A's document ID → should get 403/404
5. Logout → try to access /upload → should redirect to /login

---

## Error Responses

### Consistency Rule
**Never distinguish between "not found" and "not owned"** - return 404 for both to avoid information leakage.

```python
# WRONG - leaks information
if not doc:
    raise HTTPException(status_code=404, detail="Document not found")
if doc['user_id'] != current_user['id']:
    raise HTTPException(status_code=403, detail="Access denied")

# CORRECT - same response
if not doc or doc['user_id'] != current_user['id']:
    raise HTTPException(status_code=404, detail="Document not found")
```

---

## Database Queries

### Pattern 1: Fetch and verify owned document
```sql
SELECT * FROM documents WHERE id = ? AND user_id = ?
```

### Pattern 2: List user's documents
```sql
SELECT * FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC
```

### Pattern 3: List user's analyses
```sql
SELECT a.* FROM analyses a
JOIN documents d ON a.document_id = d.id
WHERE d.user_id = ?
```

### Pattern 4: List user's chat messages
```sql
SELECT * FROM chat_messages 
WHERE document_id IN (SELECT id FROM documents WHERE user_id = ?)
```

---

## Frontend: Protected Routes

### Step 1: Create ProtectedRoute Component

**File:** `frontend/src/components/ProtectedRoute.tsx` (NEW)

```typescript
import { Navigate } from 'react-router-dom'
import { useAppSelector } from '../hooks/redux'

interface ProtectedRouteProps {
  children: React.ReactNode
}

export default function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { token } = useAppSelector((s) => s.auth)
  
  if (!token) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}
```

### Step 2: Update App.tsx

**File:** `frontend/src/App.tsx`

```typescript
import ProtectedRoute from './components/ProtectedRoute'

function App() {
  return (
    <Routes>
      {/* Public routes */}
      <Route path="/" element={<Home />} />
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      
      {/* Protected routes */}
      <Route
        path="/upload"
        element={
          <ProtectedRoute>
            <Upload />
          </ProtectedRoute>
        }
      />
      <Route
        path="/analysis/:documentId"
        element={
          <ProtectedRoute>
            <Analysis />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        }
      />
      {/* ...more protected routes */}
    </Routes>
  )
}
```

### Step 3: Update Navbar

**File:** `frontend/src/components/Layout.tsx`

Add logout button and user menu:
```typescript
import { useAppDispatch, useAppSelector } from '../hooks/redux'
import { logout } from '../store/authSlice'

// In navbar component:
const { user, token } = useAppSelector((s) => s.auth)
const dispatch = useAppDispatch()

{token ? (
  <div className="flex items-center gap-4">
    <span>{user?.name}</span>
    <button onClick={() => dispatch(logout())}>
      Logout
    </button>
  </div>
) : (
  <Link to="/login">Login</Link>
)}
```

---

## Deployment Checklist

Before merging Phase 4D:

- [ ] All routes have ownership verification
- [ ] 404 returned for both "not found" and "not owned"
- [ ] Protected routes use ProtectedRoute wrapper
- [ ] GET /auth/me returns current user (verify token works)
- [ ] Unauthenticated requests get 401 on protected routes
- [ ] No XSS vectors in error messages
- [ ] CORS headers correct for auth
- [ ] Rate limiting works on auth endpoints
- [ ] Logout clears token properly
- [ ] Tests pass: cross-user access is blocked

---

## Rollback Plan

If ownership checks break something:

1. **Database:** All data is still there (ownership checks are read-only)
2. **Revert:** `git revert <commit>` to restore public access
3. **Root cause:** Usually a typo in user_id comparison or missing import

---

## Success Criteria

✅ Phase 4D is complete when:

1. All 24 routes have ownership verification
2. User A cannot access User B's documents (returns 403/404)
3. Frontend redirects to /login when trying to access protected routes
4. Tests confirm cross-user access is blocked
5. Deployment checklist passes
6. No new errors in Sentry

---

## Timeline

- **Day 1:** analyze.py + chat.py routes (6 routes)
- **Day 2:** upload.py + legal_id.py + property.py + business.py (13 routes)
- **Day 3:** Frontend ProtectedRoute + integration testing

**Total:** 2-3 days
