# SmartLegal-AI Session Update Protocol

Purpose: Ensure every completed work session updates ALL governance systems.

No feature, bug fix, roadmap item, or sprint is considered complete until this protocol is followed.

Last updated: 2026-05-15

---

# MANDATORY SESSION COMPLETION PROTOCOL

## STEP 1 — IMPLEMENTATION
Complete:
- Feature
- Bug fix
- Refactor
- Governance update
- Sprint milestone

---

## STEP 2 — DEVELOPMENT LOG ENTRY
Immediately add:
### DEVELOPMENT_LOG.md
Include:
- Date
- Phase
- Title
- What changed
- Files changed
- Risks
- Next priority

---

## STEP 3 — ROADMAP STATUS UPDATE
### ROADMAP_MASTER.md
- Mark:
  - [x] Completed
  - [~] In Progress
  - [!] Blocked
  - [R] Refactor

Example:
If 2B completed:
`- [x] 2B India-Specific Legal Intelligence`

---

## STEP 4 — CURRENT STATE UPDATE
### CURRENT_STATE_DIFF.md
Update:
- New features
- New dependencies
- Prompt changes
- Security changes
- Deprecated assumptions

---

## STEP 5 — MASTER CONTEXT UPDATE
### MASTER_CONTEXT.md
Required ONLY if:
- Architecture changed
- Backend flow changed
- Frontend flow changed
- AI provider changed
- Security model changed
- DB changed
- Governance changed

---

## STEP 6 — TESTING UPDATE
### TESTING_PROTOCOL.md
Required if:
- New feature
- Security boundary
- Upload/analyze/chat flow change
- AI schema change
- Auth change

---

## STEP 7 — RELEASE CHECKLIST UPDATE
### RELEASE_CHECKLIST.md
Required if:
- Release gate changed
- New route added
- New user-facing system added
- New placeholder removed
- Security gate changed

---

# UNIVERSAL RULE

## DONE ≠ CODE COMPLETE
## DONE = CODE + DOCS + ROADMAP + LOG + TEST + RELEASE GOVERNANCE UPDATED

---

# REQUIRED AI INSTRUCTION

Whenever using Claude, Codex, or ChatGPT:

“After completing any SmartLegal-AI task:
1. Update DEVELOPMENT_LOG.md
2. Update ROADMAP_MASTER.md
3. Update CURRENT_STATE_DIFF.md
4. Update MASTER_CONTEXT.md if system changed
5. Update TESTING_PROTOCOL.md if scope changed
6. Update RELEASE_CHECKLIST.md if release impacted”

---

# FAILURE CONDITIONS

A task is NOT complete if:
- Code changed but roadmap not updated
- Feature done but log missing
- Security changed but testing not updated
- Architecture changed but MASTER_CONTEXT outdated
- Release-impacting change missing checklist update

---

# MONTHLY GOVERNANCE REVIEW

Once per month:
- Audit ROADMAP_MASTER
- Audit MASTER_CONTEXT
- Audit CURRENT_STATE_DIFF
- Audit TECH DEBT
- Audit RELEASE CHECKLIST
- Archive completed sprint summaries

---

# GOLDEN RULE

SmartLegal-AI must never return to outdated documentation chaos.

Every sprint must leave the project:
## More understandable
## More secure
## More truthful
## More maintainable