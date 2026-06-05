# Google OAuth 2.0 Setup & Security

## Overview

SmartLegal-AI supports optional Google Sign-In with full OAuth 2.0 security validation.

**Security implemented:**
- ✅ Audience (aud) claim validation
- ✅ Issuer (iss) validation  
- ✅ Email verification check
- ✅ Token expiration validation
- ✅ HTTPS enforcement (production)

---

## Development Setup

### 1. Create Google OAuth Credentials

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - `http://localhost:5173` (development)
   - `https://yourdomain.com` (production)
5. Copy your **Client ID**

### 2. Configure Environment Variables

**backend/.env:**
```env
GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE.apps.googleusercontent.com
```

**frontend/.env.local:**
```env
VITE_GOOGLE_CLIENT_ID=YOUR_CLIENT_ID_HERE.apps.googleusercontent.com
```

**Important:** Both must use the same Client ID.

### 3. Start the App

**Backend:**
```bash
cd backend
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm run dev
```

### 4. Test Google Sign-In

1. Open http://localhost:5173/login
2. Click "Continue with Google"
3. Sign in with your Google account
4. You should be redirected to the Upload page
5. Verify you can upload a document

---

## Security Validations

### Audience (aud) Claim
- **What:** The token's `aud` claim must exactly match your `GOOGLE_CLIENT_ID`
- **Why:** Prevents tokens issued for other apps from being used on SmartLegal-AI
- **Error:** "Token audience mismatch"

### Issuer (iss) Claim
- **What:** Must be `https://accounts.google.com`
- **Why:** Ensures token comes from Google, not a malicious actor
- **Error:** "Invalid token issuer"

### Email Verification
- **What:** User's email must be verified (`email_verified: true`)
- **Why:** Prevents account takeover via unverified emails
- **Error:** "Email not verified by Google"

### Token Expiration
- **What:** Google's tokeninfo endpoint only accepts valid, non-expired tokens
- **Why:** Expired tokens cannot be used
- **Error:** "Invalid or expired Google token"

---

## Disabling Google OAuth

If you don't want Google Sign-In:
1. Leave `GOOGLE_CLIENT_ID` blank in backend/.env
2. Leave `VITE_GOOGLE_CLIENT_ID` blank in frontend/.env.local
3. The "Continue with Google" button will appear disabled with a tooltip
4. All attempts to use the endpoint will return 500 with "not configured" message

---

## Production Deployment

### Requirements
- [ ] GOOGLE_CLIENT_ID is set in production .env
- [ ] VITE_GOOGLE_CLIENT_ID matches GOOGLE_CLIENT_ID exactly
- [ ] Frontend domain is registered in Google Cloud Console
- [ ] HTTPS is enforced for all OAuth traffic
- [ ] Redirect URIs in Google Cloud Console include your production domain
- [ ] CORS origins include your production domain

### Checklist
```bash
# Verify credentials are set
echo $GOOGLE_CLIENT_ID  # Should not be empty

# Verify Google Cloud Console has correct redirect URIs
# https://console.cloud.google.com/apis/credentials
# Should include: https://yourdomain.com

# Verify environment matches between frontend and backend
grep VITE_GOOGLE_CLIENT_ID frontend/.env.local
grep GOOGLE_CLIENT_ID backend/.env  # Must match

# Test OAuth flow with real credentials
# 1. Visit https://yourdomain.com/login
# 2. Click "Continue with Google"
# 3. Complete sign-in
# 4. Verify successful login
```

### Monitoring
Monitor these error patterns in logs:
- `Token audience mismatch` → Config mismatch between frontend/backend
- `Invalid token issuer` → Token forged or using wrong OAuth provider
- `Email not verified` → User hasn't verified email in Google account
- `Invalid or expired Google token` → Token expired or invalid

If you see these patterns, investigate the source immediately.

---

## Testing

### Automated Tests
```bash
cd backend
python test_google_oauth.py
```

**Test results:**
- ✅ Disabled state when no CLIENT_ID
- ✅ Invalid token rejection
- ⚠️ Email validation (requires mocking - see integration tests)

### Manual Integration Test
1. **Create test account:**
   - Use a separate Google account for testing
   - Verify email in Google account settings

2. **Test happy path:**
   - Visit login page
   - Click "Continue with Google"
   - Sign in successfully
   - Verify redirected to Upload page
   - Check that user is logged in

3. **Test error cases:**
   - Try to use token from another app → should fail with audience error
   - Use wrong Client ID → should fail
   - Test with unverified email → should fail

---

## Troubleshooting

### "Google Sign-In not working"
1. Check that VITE_GOOGLE_CLIENT_ID is set and correct
2. Check that frontend domain matches Google Cloud Console
3. Check browser console for errors
4. Clear browser cache and localStorage

### "Token audience mismatch"
1. Verify GOOGLE_CLIENT_ID in backend/.env
2. Verify VITE_GOOGLE_CLIENT_ID in frontend/.env.local
3. Ensure they match exactly (copy-paste to be sure)
4. Restart both frontend and backend

### "Email not verified"
1. User needs to verify their email in Google account
2. Go to https://myaccount.google.com/security-checkup
3. Add/verify email address
4. Try sign-in again

### "Invalid or expired Google token"
1. Ensure system time is correct (clock skew)
2. Check that Google API is accessible
3. Try signing in again (old token may have expired)

---

## Security Best Practices

1. **Rotate credentials regularly:** Every 90 days minimum
2. **Monitor failed OAuth attempts:** Look for audience/issuer errors
3. **Enforce HTTPS:** Never send tokens over HTTP
4. **Keep Client ID private:** Don't commit real credentials to git
5. **Use separate OAuth apps:** Dev, staging, and production credentials
6. **Educate users:** Tell them to verify email in Google account

---

## References

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Google Identity Services](https://developers.google.com/identity/gsi/web)
- [RFC 6749 - OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- [OWASP OAuth 2.0 Security](https://cheatsheetseries.owasp.org/cheatsheets/OAuth_2_Cheat_Sheet.html)
