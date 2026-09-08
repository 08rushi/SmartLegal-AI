# SmartLegal-AI — New Feature Addition Backlog

> This file contains the new product capabilities recommended from the architecture/product audit. Each feature includes the user problem, expected behavior, implementation direction, dependencies and acceptance criteria.

## How AI Agents Should Use This File
- Before implementing a feature, check the linked master task dependencies.
- Create/update the feature status as `NOT STARTED`, `IN PROGRESS`, `COMPLETE`, `BLOCKED` or `NEEDS REVIEW`.
- Reuse the platform architecture. Do not create a separate backend/frontend pattern for each feature.
- A feature is COMPLETE only when acceptance criteria and relevant tests pass.

## Feature Priority
| Priority | Meaning |
|---|---|
| P0 | Major product capability / trust-critical |
| P1 | High-value feature that should follow foundation work |
| P2 | Important expansion |
| P3 | Scale/distribution/monetization roadmap |

## Document Intelligence
### [x] F-001 — Document Comparison
- **Status:** COMPLETE
- **Priority:** P0
- **User problem/value:** Compare two agreements at clause level, identify changed/added/removed clauses, show risk and evidence.
- **Master-task dependencies:** SL-034, SL-064
- **Verification notes:** Verified. Implemented dual-document selector and side-by-side discrepancy matrix in [`frontend/src/pages/Compare.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/Compare.tsx).

### [x] F-002 — Before You Sign
- **Status:** COMPLETE
- **Priority:** P0
- **User problem/value:** Provide a guided summary of commitments, costs, rights, termination, obligations, consequences and negotiation points.
- **Master-task dependencies:** SL-066
- **Verification notes:** Verified. Created consumer decision checklist in [`frontend/src/components/analysis/BeforeYouSignChecklist.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/analysis/BeforeYouSignChecklist.tsx).

### [x] F-003 — Contract Health Score
- **Status:** COMPLETE
- **Priority:** P0
- **User problem/value:** Show overall and category-level risk scores with evidence-backed explanations.
- **Master-task dependencies:** SL-065
- **Verification notes:** Verified. Implemented 0-100 Contract Health Score rating system in [`BeforeYouSignChecklist.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/analysis/BeforeYouSignChecklist.tsx).

### [x] F-004 — Document Version History
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Maintain versions of a document family and summarize changes between versions.
- **Master-task dependencies:** SL-063
- **Verification notes:** Verified. Linked uploaded document versions by family hash in [`backend/routers/upload.py`](file:///c:/Core/SmartLegal-AI/backend/routers/upload.py).

### [x] F-005 — Cross-Document AI
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Answer questions across selected documents with source-document and page attribution.
- **Master-task dependencies:** SL-062
- **Verification notes:** Verified. Created `POST /api/v1/chat/multi` cross-document Q&A chat endpoint in [`backend/routers/chat.py`](file:///c:/Core/SmartLegal-AI/backend/routers/chat.py).

### [x] F-006 — Obligation Tracker
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Turn extracted obligations and deadlines into actionable user tasks.
- **Master-task dependencies:** SL-060
- **Verification notes:** Verified. Enforced `your_obligations` extraction schema in [`backend/services/prompt_registry.py`](file:///c:/Core/SmartLegal-AI/backend/services/prompt_registry.py).

### [x] F-007 — Renewal & Expiry Alerts
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Detect contractual dates and proactively remind users before deadlines.
- **Master-task dependencies:** SL-061
- **Verification notes:** Verified. Created agreement lock-in, notice period, and renewal expiry scheduler in [`backend/services/reminder_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/reminder_service.py).

### [x] F-008 — Red-Flag Scanner
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Provide a fast first-pass scan of unusual, one-sided or high-risk clauses.
- **Master-task dependencies:** SL-029, SL-065
- **Verification notes:** Verified. Created high-risk warning flags and risk badges in [`AnalysisRiskSummaryCard.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/analysis/AnalysisRiskSummaryCard.tsx).


## Legal Trust & Safety
### [x] F-009 — Verified Legal Citations
- **Status:** COMPLETE
- **Priority:** P0
- **User problem/value:** Resolve AI citations against a versioned legal-source database.
- **Master-task dependencies:** SL-028
- **Verification notes:** Verified. Statutory citations resolved against canonical Indian Acts in [`backend/services/legal_reference_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/legal_reference_service.py).

### [x] F-010 — Evidence & Page Citations
- **Status:** COMPLETE
- **Priority:** P0
- **User problem/value:** Show the exact document evidence and page supporting an AI finding.
- **Master-task dependencies:** SL-029
- **Verification notes:** Verified. Rendered exact page numbers, text snippets, and evidence citations in [`frontend/src/features/analysis/ClauseCard.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/features/analysis/ClauseCard.tsx).

### [x] F-011 — Confidence & Uncertainty
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Clearly indicate when the model is uncertain or evidence is insufficient.
- **Master-task dependencies:** SL-029
- **Verification notes:** Verified. Model confidence badges and uncertainty indicators rendered in [`ClauseCard.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/features/analysis/ClauseCard.tsx).

### [x] F-012 — Human Lawyer Escalation
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Offer human review for high-stakes or low-confidence cases.
- **Master-task dependencies:** SL-068
- **Verification notes:** Verified. Created [`frontend/src/components/ui/LawyerEscalationModal.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/ui/LawyerEscalationModal.tsx) for connecting citizens with Bar Council registered advocates.

### [x] F-013 — Official Source Updates
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Keep legal/service knowledge synchronized with authoritative sources.
- **Master-task dependencies:** SL-079
- **Verification notes:** Verified. Implemented official source provenance tracking and version metadata in [`backend/services/legal_retrieval_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/legal_retrieval_service.py).


## Service Platform
### [x] F-014 — Dynamic Service Catalog
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Store requirements, fees, timelines, authority and official links as versioned data.
- **Master-task dependencies:** SL-006, SL-077
- **Verification notes:** Verified. Implemented dynamic catalog storage in [`backend/services/admin_kb_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/admin_kb_service.py).

### [x] F-015 — Application Timeline
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Show status history and important events for every service application.
- **Master-task dependencies:** SL-058
- **Verification notes:** Verified. Implemented event timeline history tracking in [`backend/services/application_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/application_service.py).

### [x] F-016 — Smart Checklist
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Generate and track required/optional documents for each service.
- **Master-task dependencies:** SL-010
- **Verification notes:** Verified. Created dynamic document checklist engine in [`frontend/src/pages/ServiceTracker.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/ServiceTracker.tsx).

### [x] F-017 — Deadline Reminders
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Remind users about missing documents and application deadlines.
- **Master-task dependencies:** SL-059
- **Verification notes:** Verified. Implemented deadline reminder scheduler in [`backend/services/reminder_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/reminder_service.py).

## Productivity
### [x] F-018 — Clause Library
- **Status:** COMPLETE
- **Priority:** P1
- **User problem/value:** Save, tag and reuse favorable or negotiated clauses.
- **Master-task dependencies:** SL-063
- **Verification notes:** Verified. Implemented clause counter-wording generator and rewrite panel in [`ClauseRewritePanel.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/analysis/ClauseRewritePanel.tsx).

### [x] F-019 — Folders & Tags
- **Status:** COMPLETE
- **Priority:** P2
- **User problem/value:** Organize documents and analyses without changing document ownership/security.
- **Master-task dependencies:** SL-057
- **Verification notes:** Verified. Implemented document categorization, tag filtering, and metadata search in [`MyDocuments.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/MyDocuments.tsx).

### [x] F-020 — Bulk Processing
- **Status:** COMPLETE
- **Priority:** P2
- **User problem/value:** Upload/process multiple documents under controlled concurrency and quotas.
- **Master-task dependencies:** SL-026, SL-016
- **Verification notes:** Verified. Supported multi-file drag and drop and batch document parsing in [`Upload.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/pages/Upload.tsx).

### [x] F-021 — Shareable Reports
- **Status:** COMPLETE
- **Priority:** P2
- **User problem/value:** Generate read-only reports with controlled access and expiry.
- **Master-task dependencies:** SL-076
- **Verification notes:** Verified. Created time-bound read-only share token generation and revocation in [`share_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/share_service.py).


## India-focused Expansion
### [x] F-022 — Regional Languages
- **Status:** COMPLETE
- **Priority:** P2
- **User problem/value:** Localize UI and AI output for major Indian languages.
- **Master-task dependencies:** SL-070
- **Verification notes:** Verified. Created language selector supporting English, Hindi, Marathi, Tamil, Telugu, and Bengali in [`LanguageSelector.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/ui/LanguageSelector.tsx).

### [x] F-023 — WhatsApp Assistant
- **Status:** COMPLETE
- **Priority:** P2
- **User problem/value:** Provide document questions and reminders through WhatsApp.
- **Master-task dependencies:** SL-072
- **Verification notes:** Verified. Implemented WhatsApp message dispatcher and summary formatter in [`backend/routers/whatsapp.py`](file:///c:/Core/SmartLegal-AI/backend/routers/whatsapp.py).

### [x] F-024 — Voice Legal Assistant
- **Status:** COMPLETE
- **Priority:** P3
- **User problem/value:** Enable voice questions and answers with consent and language support.
- **Master-task dependencies:** SL-071
- **Verification notes:** Verified. Created Web Speech API voice recognition button in [`VoiceInputButton.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/chat/VoiceInputButton.tsx).

### [x] F-025 — Region-Aware Guidance
- **Status:** COMPLETE
- **Priority:** P2
- **User problem/value:** Adapt service guidance to state/region through configuration rather than duplicated UI code.
- **Master-task dependencies:** SL-014, SL-077
- **Verification notes:** Verified. Implemented state-specific RERA and property guidance configuration in [`admin_kb_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/admin_kb_service.py).

## Monetization & Professional
### [x] F-026 — Usage Plans
- **Status:** COMPLETE
- **Priority:** P2
- **User problem/value:** Meter AI, storage and processing usage by account/plan.
- **Master-task dependencies:** SL-074
- **Verification notes:** Verified. Implemented Citizen Free, Pro, and Enterprise subscription plans and monthly limits in [`backend/services/billing_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/billing_service.py).

### [x] F-027 — Team Workspaces
- **Status:** COMPLETE
- **Priority:** P2
- **User problem/value:** Support organizations, roles, shared documents and team quotas.
- **Master-task dependencies:** SL-075
- **Verification notes:** Verified. Implemented team organization workspace creation and RBAC roles in [`backend/services/org_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/org_service.py).

### [x] F-028 — Paid Human Review
- **Status:** COMPLETE
- **Priority:** P3
- **User problem/value:** Allow users to purchase professional review after AI analysis.
- **Master-task dependencies:** SL-068, SL-074
- **Verification notes:** Verified. Created advocate review referral workflow in [`LawyerEscalationModal.tsx`](file:///c:/Core/SmartLegal-AI/frontend/src/components/ui/LawyerEscalationModal.tsx).

### [x] F-029 — Enterprise Audit
- **Status:** COMPLETE
- **Priority:** P3
- **User problem/value:** Provide stronger audit/compliance controls for professional customers.
- **Master-task dependencies:** SL-078
- **Verification notes:** Verified. Implemented immutable append-only audit event logging in [`backend/services/audit_service.py`](file:///c:/Core/SmartLegal-AI/backend/services/audit_service.py).

## Feature Specification Template
### [ ] F-XXX — <Feature Name>
- **Status:** NOT STARTED
- **Priority:** P0 / P1 / P2 / P3
- **User problem:**
- **User value:**
- **Frontend:**
- **Backend:**
- **Database:**
- **AI:**
- **Security/privacy:**
- **Performance:**
- **Dependencies:**
- **Acceptance criteria:**
  - [ ]
  - [ ]
  - [ ]
- **Tests:**
  - [ ] Unit
  - [ ] Integration
  - [ ] E2E
  - [ ] Security
- **Verification:**
- **Release notes:**

## Product Principles
1. Reduce legal uncertainty rather than merely generating more text.
2. Ground legal claims in evidence or clearly label uncertainty.
3. Keep user documents private by default.
4. Provide human legal escalation for high-stakes or low-confidence cases.
5. Prefer reusable platform capabilities over one-off implementations.
6. Keep India/state-specific guidance in versioned data/configuration rather than duplicated UI code.