# Meta WhatsApp Cloud API — Live Sandbox Verification Runbook

> **Document Status**: Final — Step 3E.2 Approved
> **Scope**: Authoritative procedure for executing the REAL Meta WhatsApp Cloud API Sandbox against the SmartLegal-AI implementation.
> **Secret Policy**: No real credentials appear in this document at any point. Use `<PLACEHOLDER>` values as reminders only.

> [!CAUTION]
> **NEVER commit real Meta credentials to source control.** Store all secrets locally in `backend/.env` which is listed in `.gitignore`. Do not paste real values into this document, chat messages, issues, or pull requests.

---

## 1. Purpose and Scope

This runbook validates that the SmartLegal-AI WhatsApp integration is correctly connected to the Meta WhatsApp Cloud API in a Sandbox (non-production) environment.

**This runbook:**
- Provides step-by-step environment setup and configuration
- Covers all 13 live test scenarios (A–M)
- Documents expected HTTP, application, and database behavior for each test
- Documents known production gaps that do not block Sandbox testing
- Provides a final sign-off checklist

**This runbook does NOT:**
- Provide real Meta credentials
- Apply to production deployments (separate approval required)
- Cover WhatsApp Business API (WABA) template message configuration

---

## 2. Current Architecture

```
Meta WhatsApp Cloud API (Sandbox)
    |
    |  POST /api/v1/whatsapp/webhook
    |  X-Hub-Signature-256: sha256=<hmac>
    v
backend/routers/whatsapp.py
    +-- verify_meta_signature_and_get_raw_body()
    |       Raw-byte streaming (1 MB ceiling)
    |       HMAC-SHA256 verification (constant-time)
    |       Production: fail-closed if APP_SECRET absent (HTTP 503)
    |
    +-- GET /webhook  -- Hub verification (hub.challenge)
    |
    +-- POST /webhook -- Meta event receiver
            |
            +-- MetaWhatsAppAdapter.extract_inbound_payloads()
            |       Payload normalization, wamid enforcement, status filtering
            |
            +-- claim_message_processing()  -- Step 2G atomic claim
            |
            +-- FastAPI BackgroundTasks.add_task()  -- HTTP 200 returned here
            |
            +-- _process_inbound_background()
                    Independent DB context (get_db_ctx)
                    |
                    +-- WhatsAppOrchestrator.process_inbound_message()
                            Steps 1-7
                            |
                            +-- send_outbound_message()
                                    Idempotency key + outbound claim
                                    MetaWhatsAppOutboundAdapter
                                    POST /{phone_number_id}/messages
```

---

## 3. Preconditions

Before beginning live Sandbox testing, confirm ALL of the following:

**Code:**
- [ ] `pytest` suite: 0 failures (baseline >= 155 tests after Step 3E.2)
- [ ] `npm run lint`: 0 errors
- [ ] `npm run build`: clean build, no errors
- [ ] No real credentials committed to git (`git log --all -S "EAAG"` returns 0 results)

**Meta Developer Account:**
- [ ] Active Meta Developer account with a confirmed WhatsApp Business Account (WABA)
- [ ] A test phone number configured in the Meta Dashboard (your personal number or a test number)
- [ ] The App is in **Development mode** (not Live mode) for Sandbox testing

**Infrastructure:**
- [ ] Backend starts cleanly on `http://localhost:8000`
- [ ] Frontend starts cleanly on `http://localhost:5173`
- [ ] HTTPS tunnel tool installed (ngrok, Cloudflare Tunnel, or equivalent)

---

## 4. Environment Configuration

### 4.1 Backend `.env`

Copy `backend/.env.example` to `backend/.env` and fill in the following values from your Meta Developer Dashboard. Do not commit `.env` to source control.

```env
META_WHATSAPP_VERIFY_TOKEN=<YOUR_META_VERIFY_TOKEN>
META_WHATSAPP_ACCESS_TOKEN=<YOUR_META_ACCESS_TOKEN>
META_WHATSAPP_APP_SECRET=<YOUR_META_APP_SECRET>
META_WHATSAPP_PHONE_NUMBER_ID=<YOUR_META_PHONE_NUMBER_ID>
META_WHATSAPP_API_VERSION=v21.0
META_WHATSAPP_GRAPH_URL=https://graph.facebook.com
```

> [!IMPORTANT]
> **API Version**: Confirm the version currently configured in `backend/config.py` and `backend/.env.example` is still supported by Meta before live execution. If Meta requires a newer supported version, update only `META_WHATSAPP_API_VERSION` in your local `.env` as a separate approved change. Do not silently change the default in `config.py`.

> [!IMPORTANT]
> **Production Environment Guard**: Set `ENVIRONMENT=development` in `.env` for Sandbox testing. With `ENVIRONMENT=production`, a missing `META_WHATSAPP_APP_SECRET` will return HTTP 503 on all webhook POST requests (correct fail-closed behavior — Step 3E.2).

### 4.2 Where to Find Each Value

| Variable | Location in Meta Dashboard |
|---|---|
| `META_WHATSAPP_VERIFY_TOKEN` | You choose — any strong random string (e.g. output of `openssl rand -hex 16`) |
| `META_WHATSAPP_ACCESS_TOKEN` | Meta App Dashboard -> WhatsApp -> API Setup -> Temporary access token (or permanent System User token) |
| `META_WHATSAPP_APP_SECRET` | Meta App Dashboard -> App Settings -> Basic -> App Secret (click "Show") |
| `META_WHATSAPP_PHONE_NUMBER_ID` | Meta App Dashboard -> WhatsApp -> API Setup -> Phone number section -> Phone Number ID |
| `META_WHATSAPP_API_VERSION` | Use the version shown in the Meta Dashboard API test console |
| `META_WHATSAPP_GRAPH_URL` | Fixed: `https://graph.facebook.com` |

---

## 5. Meta Developer Dashboard Configuration

Perform these configuration steps in the Meta Developer Portal (https://developers.facebook.com/apps/).

### 5.1 App & WABA Setup
1. Navigate to your App -> **WhatsApp** section in the left sidebar.
2. Confirm your WhatsApp Business Account (WABA) is linked.
3. Confirm a phone number is configured under **API Setup** (the Sandbox test phone number).
4. Copy the **Phone Number ID** — this is `<YOUR_META_PHONE_NUMBER_ID>`.

### 5.2 Test Recipient Setup
1. In **WhatsApp -> API Setup**, find the **"To" field** (recipient phone number).
2. Add your personal phone number as a test recipient (Meta will send a verification code to the WhatsApp app on that number).
3. This recipient number is `<YOUR_TEST_RECIPIENT_NUMBER>`.

### 5.3 Webhook Callback URL and Verify Token
*(These are set after the HTTPS tunnel is running — see Section 6.)*

1. Navigate to **WhatsApp -> Configuration**.
2. Set **Callback URL**: `<YOUR_HTTPS_TUNNEL_URL>/api/v1/whatsapp/webhook`
3. Set **Verify Token**: exact value from `META_WHATSAPP_VERIFY_TOKEN` in your `.env`.
4. Click **Verify and Save** (the backend must be running first).

### 5.4 Webhook Field Subscription
1. In **WhatsApp -> Configuration -> Webhook fields**, enable the **`messages`** field.
2. This subscribes your app to receive inbound user message webhooks.

> [!NOTE]
> **WABA Subscription**: Enabling webhook fields in the Dashboard is separate from the programmatic WABA subscription API call. For Sandbox testing, the Dashboard UI subscription is sufficient. For a programmatic subscription, use:
>
> ```
> POST https://graph.facebook.com/<API_VERSION>/<YOUR_WABA_ID>/subscribed_apps
> Authorization: Bearer <YOUR_META_ACCESS_TOKEN>
> ```

---

## 6. HTTPS Tunnel Setup

Meta requires a publicly reachable HTTPS endpoint to deliver webhook events. Use a tunnel to expose your local backend.

### Using ngrok (example)
```bash
# Install ngrok from https://ngrok.com/download
ngrok http 8000
# Note the Forwarding URL: https://xxxx.ngrok-free.app
```

### Using Cloudflare Tunnel (alternative)
```bash
cloudflared tunnel --url http://localhost:8000
```

Your tunnel URL is `<YOUR_HTTPS_TUNNEL_URL>`.

> [!IMPORTANT]
> Free ngrok tunnels generate a new subdomain on every restart. If your tunnel restarts, you must update the Callback URL in the Meta Dashboard and re-run Test B (webhook verification).

---

## 7. Backend Startup

```bash
cd backend
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

uvicorn main:app --reload --port 8000
```

**Verify startup logs do NOT contain:**
- Any string starting with `EAAG`
- The value of `META_WHATSAPP_APP_SECRET`
- The value of `META_WHATSAPP_VERIFY_TOKEN`
- The value of `META_WHATSAPP_ACCESS_TOKEN`

The only credential-adjacent output should be `DATABASE_URL` with the password masked as `********`.

---

## 8. WABA/Webhook Subscription Verification

Before the live tests, confirm webhook subscription state:

1. In Meta Dashboard -> WhatsApp -> Configuration, the Callback URL field shows `<YOUR_HTTPS_TUNNEL_URL>/api/v1/whatsapp/webhook` with a green **verified** checkmark.
2. The **`messages`** webhook field is enabled (checked).

If the callback URL shows "Not verified", proceed to Test B first.

---

## --- CONFIGURATION COMPLETE — LIVE EXECUTION BEGINS ---

---

## 9. Live Test Matrix

All tests must be executed in order. Mark [PASS] or [FAIL] for each item.

---

### Test A — Environment Startup & Pre-Flight

| # | Action | Expected |
|---|---|---|
| A1 | Start backend: `uvicorn main:app --reload --port 8000` | Server starts on port 8000 without import errors |
| A2 | Review startup console output | No credentials visible in logs |
| A3 | Start HTTPS tunnel | Public HTTPS URL obtained |
| A4 | Open `<YOUR_HTTPS_TUNNEL_URL>/docs` in browser | FastAPI Swagger UI loads |
| A5 | GET `/api/v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=WRONG&hub.challenge=test` | HTTP 403 — endpoint is live and rejecting wrong token |

**Pass criteria**: All 5 items green. No credential leakage in logs.
- [ ] A PASS / FAIL: ___

---

### Test B — Webhook GET Verification (Hub Handshake)

**Action**: In Meta Dashboard -> WhatsApp -> Configuration, enter the Callback URL and Verify Token, then click **Verify and Save**.

**Expected HTTP behavior**: Meta sends `GET /api/v1/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=<YOUR_META_VERIFY_TOKEN>&hub.challenge=<RANDOM_STRING>` -> SmartLegal responds HTTP 200 with `hub.challenge` as plain text body.

**Expected application behavior**: Meta Dashboard shows green verified checkmark on Callback URL.

**Expected DB behavior**: No database records created.

**Verification**:
- [ ] Meta Dashboard shows green verified checkmark
- [ ] Backend logs show: `GET /api/v1/whatsapp/webhook` 200

- [ ] B PASS / FAIL: ___

---

### Test C — English Inbound Text Message

**Action**: From `<YOUR_TEST_RECIPIENT_NUMBER>`, send the text message `Hello` to the Meta Test Business number.

**Expected HTTP behavior**: Meta delivers `POST /api/v1/whatsapp/webhook` with valid `X-Hub-Signature-256` -> SmartLegal returns HTTP 200 in < 100ms.

**Expected application behavior**:
1. HMAC signature verified from raw bytes
2. `wamid` extracted from payload
3. Step 2G claim acquired in `whatsapp_message_processing`
4. Background orchestrator executes asynchronously
5. `MetaWhatsAppOutboundAdapter` sends reply to Meta Graph API
6. User receives reply message on their WhatsApp device

**Expected DB behavior**:
- `whatsapp_contacts`: 1 row with `phone_number = <YOUR_TEST_RECIPIENT_NUMBER>` (E.164 format)
- `whatsapp_message_processing`: 1 row with `provider_message_id = <wamid>`, `processing_status = 'completed'`
- `whatsapp_outbound_messages`: 1 row with `delivery_status = 'sent'`, `provider_message_id = wamid.outbound...`

**Verification**:
- [ ] User device receives reply on WhatsApp
- [ ] `whatsapp_message_processing` row has `processing_status = 'completed'`
- [ ] `whatsapp_outbound_messages` row has `delivery_status = 'sent'`
- [ ] Logs show no credential leakage

- [ ] C PASS / FAIL: ___

---

### Test D — Language Onboarding

**Action**: Send the following messages sequentially (allow each reply before sending the next):
1. Send `2` -> Expected: Hindi onboarding menu
2. Send `3` -> Expected: Marathi onboarding menu
3. Send `1` -> Expected: English confirmation

**Expected HTTP behavior**: Each message -> HTTP 200 fast ack.

**Expected application behavior**: Each selection triggers the language onboarding flow; user receives a confirmation reply in the selected language.

**Expected DB behavior**:
- `whatsapp_contacts`: `preferred_language` updated to reflect final selection
- 3 rows in `whatsapp_message_processing` (all `completed`)
- At least 3 rows in `whatsapp_outbound_messages` (all `sent`)

- [ ] D PASS / FAIL: ___

---

### Test E — Legal Q&A

**Action**: After completing language selection, send: `Can my landlord withhold my security deposit?`

**Expected HTTP behavior**: HTTP 200 fast ack.

**Expected application behavior**: AI-generated legal response received on WhatsApp within 10–30 seconds.

**Expected DB behavior**:
- 1 new row in `whatsapp_message_processing` (completed)
- 1 new row in `whatsapp_outbound_messages` (sent)

- [ ] E PASS / FAIL: ___

---

### Test F — PDF Document Intake

**Action**: Send a PDF document (e.g. `rental_agreement.pdf`, max 10 MB) from the test number.

**Expected HTTP behavior**: Meta delivers document webhook with `media_id` -> HTTP 200 fast ack.

**Expected application behavior**:
1. `document` type extracted with `media_id`
2. `MetaMediaDownloader` calls `GET https://graph.facebook.com/<API_VERSION>/<media_id>` with Bearer token
3. Meta returns download URL on `*.fbcdn.net` or `*.fbsbx.com` domain
4. SSRF validation passes
5. Authenticated stream download completes
6. Magic bytes validated (`%PDF`)
7. AI analysis executes
8. Summary reply sent to user on WhatsApp

**Expected DB behavior**:
- 1 row in `whatsapp_message_processing` (completed)
- 1 row in `whatsapp_outbound_messages` (sent)
- 1 row in `documents` table (status: completed)

**Verification**:
- [ ] User receives document summary reply on WhatsApp
- [ ] `documents` table has 1 new row
- [ ] Logs show SSRF-validated download URL (fbcdn.net or fbsbx.com)

- [ ] F PASS / FAIL: ___

---

### Test G — Image Document Intake

**Action**: Send a JPG or PNG photo of a contract or legal notice from the test number.

**Expected HTTP behavior**: `image` type webhook with `media_id` -> HTTP 200 fast ack.

**Expected application behavior**: Same pipeline as Test F — `image` extraction, `MetaMediaDownloader`, SSRF, magic-byte validation, OCR, AI analysis, reply.

**Expected DB behavior**: Same pattern as Test F.

- [ ] G PASS / FAIL: ___

---

### Test H — Active Document Context (Follow-up Q&A)

**Action**: Immediately after Test F, send: `What are the 3 biggest risks in this document?`

**Expected HTTP behavior**: HTTP 200 fast ack.

**Expected application behavior**: AI responds with risk-specific analysis referencing the document from Test F (active document context preserved within session).

**Expected DB behavior**:
- 1 new row in `whatsapp_message_processing` (completed)
- 1 new row in `whatsapp_outbound_messages` (sent)

- [ ] H PASS / FAIL: ___

---

### Test I — Progressive Drafting

**Action**: Send `I need a rental agreement draft` from the test number.

**Expected HTTP behavior**: HTTP 200 fast ack.

**Expected application behavior**: Orchestrator initiates guided drafting workflow — presents requirement collection prompts.

**Expected DB behavior**:
- 1 new row in `whatsapp_message_processing` per inbound message
- 1 new row in `whatsapp_outbound_messages` per outbound reply

- [ ] I PASS / FAIL: ___

---

### Test J — Duplicate Webhook Replay (Idempotency)

**Action**: Replay the exact same webhook POST body from Test C (use ngrok replay or recompute HMAC and curl).

**Expected HTTP behavior**: HTTP 200 returned.

**Expected application behavior**:
1. `claim_message_processing` finds existing `completed` record for the wamid
2. Returns `is_owner: False` — no orchestrator invocation, no LLM call
3. No outbound message dispatched

**Expected DB behavior**:
- `whatsapp_message_processing`: row count unchanged (same wamid, 1 row only)
- `whatsapp_outbound_messages`: row count unchanged

**Verification**:
- [ ] No new `whatsapp_message_processing` row created
- [ ] No new `whatsapp_outbound_messages` row created
- [ ] No second reply received on the test phone

- [ ] J PASS / FAIL: ___

---

### Test K — Status Callback Observation

**Action**: After Tests C–J, observe Meta delivery status callbacks in ngrok inspector.

**Expected HTTP behavior**: SmartLegal returns HTTP 200 for each status callback.

**Expected application behavior**: Status events with `statuses` key (no `messages` key) -> filtered by `extract_inbound_payloads()` -> response `{"status": "ignored", "detail": "Non-message or status notification event"}`.

**Expected DB behavior**: No new rows in `whatsapp_message_processing`. No new rows in `whatsapp_outbound_messages`.

> [!NOTE]
> **KNOWN PRODUCTION GAP**: Status callbacks (sent/delivered/read/failed) are currently recognized and filtered correctly but are NOT persisted back into `whatsapp_outbound_messages.delivery_status`. The delivery status in the DB reflects the outbound dispatch result only.
>
> **Future Enhancement Item**: Implement a dedicated status callback handler that updates `whatsapp_outbound_messages.delivery_status` based on incoming `statuses` events. This requires a new inbound processing path separate from the Step 2G inbound claim logic.

**Verification**:
- [ ] Backend logs show `"Non-message or status notification event"` for status callbacks
- [ ] No new DB rows created for status callbacks

- [ ] K PASS / FAIL: ___

---

### Test L — Failure and Security Behavior

**L1 — Invalid HMAC signature -> HTTP 401**
```bash
curl -X POST <YOUR_HTTPS_TUNNEL_URL>/api/v1/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=0000000000000000000000000000000000000000000000000000000000000000" \
  -d '{"object":"whatsapp_business_account","entry":[]}'
```
Expected: HTTP 401. No business processing.
- [ ] L1 PASS / FAIL: ___

**L2 — Missing signature header -> HTTP 401**
```bash
curl -X POST <YOUR_HTTPS_TUNNEL_URL>/api/v1/whatsapp/webhook \
  -H "Content-Type: application/json" \
  -d '{"object":"whatsapp_business_account","entry":[]}'
```
Expected: HTTP 401 (when `META_WHATSAPP_APP_SECRET` is configured). No business processing.
- [ ] L2 PASS / FAIL: ___

**L3 — Oversized body -> HTTP 413**

Send a body larger than 1 MB. Expected: HTTP 413 before JSON parsing. No business processing.
- [ ] L3 PASS / FAIL: ___

**L4 — Malformed JSON -> HTTP 400**

Send a request with a valid HMAC but non-JSON body bytes. Expected: HTTP 400 Bad Request.
- [ ] L4 PASS / FAIL: ___

**L5 — Webhook with missing wamid -> ignored, HTTP 200**

Send a webhook with a valid HMAC and a `messages` array entry without an `id` field. Expected: HTTP 200 `{"status": "ok", "processed_count": 0}`. No Step 2G claim created.
- [ ] L5 PASS / FAIL: ___

- [ ] L PASS / FAIL: ___

---

### Test M — Security and Log Verification

**M1 — Application log review**: Search uvicorn output for credential strings. Expected: 0 matches for real values; `[MASKED_TOKEN]` is acceptable in error log lines.
- [ ] M1 PASS / FAIL: ___

**M2 — Database content review**: Confirm no message body content stored in `last_error_code` or `last_error_class` columns.
- [ ] M2 PASS / FAIL: ___

**M3 — ngrok request inspector review**: Confirm no Authorization header values or app_secret strings appear in response bodies.
- [ ] M3 PASS / FAIL: ___

- [ ] M PASS / FAIL: ___

---

## 10. Database Observability

### Expected State After Completing Tests A–M

**`whatsapp_contacts`**: 1 row per unique test recipient phone number in E.164 format.

**`whatsapp_message_processing`**:
- 1 row per unique inbound `wamid`
- `processing_status = 'completed'` for successfully processed messages
- `processing_status = 'failed'` for messages where orchestration raised an exception
- `processing_status = 'processing'` should not persist beyond 120s (stale recovery)
- Duplicate wamid -> row count does NOT increase (idempotency guard)

**`whatsapp_outbound_messages`**:
- 1 or more rows per dispatched outbound reply
- `delivery_status = 'sent'` when Meta Graph API accepted the message
- `delivery_status = 'failed_non_retryable'` for 4xx responses
- `delivery_status = 'failed_retryable'` for 5xx responses
- `delivery_status = 'unknown'` for connection timeouts
- `provider_message_id`: real Meta outbound wamid from Meta Graph API response

**`documents`**: 1 row per successfully processed PDF or image document.

**Duplicate Inbound Verification Query**:
```sql
SELECT provider_message_id, COUNT(*) AS row_count
FROM whatsapp_message_processing
GROUP BY provider_message_id
HAVING COUNT(*) > 1;
```
Expected: 0 rows (no duplicate processing records).

---

## 11. Troubleshooting

| Symptom | Likely Cause | Resolution |
|---|---|---|
| Meta Dashboard shows "Failed to verify webhook" | Backend not running, tunnel URL wrong, or verify token mismatch | Check backend; confirm Callback URL and Verify Token match `.env` exactly |
| HTTP 503 on webhook POST | `META_WHATSAPP_APP_SECRET` blank AND `ENVIRONMENT=production` | Add App Secret to `.env` or set `ENVIRONMENT=development` for sandbox |
| HTTP 401 on webhook POST | App Secret mismatch or wrong HMAC | Confirm App Secret in `.env` matches Meta Dashboard exactly |
| HTTP 401 on GET verification | Verify token mismatch | Confirm `META_WHATSAPP_VERIFY_TOKEN` matches Meta Dashboard exactly |
| No reply received on phone | Missing outbound credentials | Confirm `META_WHATSAPP_ACCESS_TOKEN` and `META_WHATSAPP_PHONE_NUMBER_ID` in `.env` |
| `delivery_status = 'failed_non_retryable'` | Recipient not in Sandbox recipient list | Add test recipient in Meta Dashboard -> API Setup |
| Media download 401 | Access token expired | Refresh `META_WHATSAPP_ACCESS_TOKEN` (temporary tokens expire in 24h) |
| Media URL SSRF rejection | Meta returned non-whitelisted domain | Report as a bug — do NOT relax the SSRF whitelist |
| Duplicate outbound messages appear | Idempotency broken | Check `whatsapp_message_processing` and `whatsapp_outbound_messages` for duplicate rows |
| `400 Bad Request` on outbound send | Phone number format incorrect | Confirm `normalize_phone_number()` returns number without `+` prefix |

---

## 12. Log / Security Verification Checklist

Run the following checks against application logs before signing off:

```
[ ] grep -r "EAAG" backend/        -> 0 results (no hardcoded tokens)
[ ] grep "Bearer " <uvicorn log>   -> 0 results
[ ] grep "app_secret" <uvicorn log> -> only configuration field names, never values
[ ] grep "verify_token" <uvicorn log> -> only field names, never actual token values
```

**Acceptable** log output examples:
```
[whatsapp-router] HMAC signature mismatch for inbound Meta webhook.
[meta-outbound-adapter] Non-retryable Meta 4xx error (400): Invalid recipient [MASKED_TOKEN]
[whatsapp-reliability] Event wamid.HBgLxxx already completed. Reusing persisted reply.
```

**NOT acceptable** (indicates credential leakage — file a bug immediately):
```
META_WHATSAPP_APP_SECRET = a1b2c3...
Authorization: Bearer EAAG...
verify_token = my_actual_token_value
```

---

## 13. Final Sign-Off Checklist

### Pre-Execution
- [ ] `pytest` baseline passed (>= 155 tests, 0 failures)
- [ ] `npm run build` clean
- [ ] `.env` configured with real Sandbox credentials
- [ ] No credentials committed to git

### Configuration
- [ ] Meta Dashboard Callback URL verified (green checkmark)
- [ ] `messages` webhook field enabled
- [ ] Test recipient number added to Sandbox

### Live Test Results
- [ ] A — Startup / preflight [PASS]
- [ ] B — Webhook GET verification [PASS]
- [ ] C — Inbound English text + outbound reply on device [PASS]
- [ ] D — Language onboarding (all 3 languages) [PASS]
- [ ] E — Legal Q&A [PASS]
- [ ] F — PDF document intake + summary reply [PASS]
- [ ] G — Image document intake [PASS]
- [ ] H — Active document context follow-up [PASS]
- [ ] I — Progressive drafting workflow [PASS]
- [ ] J — Duplicate wamid replay: 0 additional DB rows, 0 duplicate replies [PASS]
- [ ] K — Status callbacks: ignored correctly [PASS]
- [ ] L — Security failure behaviors (L1-L5) [PASS]
- [ ] M — Log and DB security verification [PASS]

### Known Non-Blocking Production Gaps (do not block Sandbox sign-off)
- [WARNING] Status callback delivery status not persisted to `whatsapp_outbound_messages` (KNOWN GAP — Test K)
- [WARNING] No retry queue for `failed_retryable` outbound messages (orchestrator does not retry automatically)

### Final Verdict
- [ ] All 13 test groups PASS
- [ ] 0 credential leakage findings
- [ ] DB observability verified

**Sandbox verification sign-off**: ___________________________
**Date**: ___________________________
**Executor**: ___________________________

---

*After this runbook is completed successfully, update `docs/CHANGELOG_AND_WORK_LOG.md` with session notes and change the project status from "Live Meta Sandbox verification pending" to "Live Meta Sandbox verification complete" in `docs/PROJECT_STATUS_AND_ROADMAP.md`.*
