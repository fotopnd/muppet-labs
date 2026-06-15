# Planner Output — red-team-platform v5

**Role:** planner
**Sequence:** add-feature
**Date:** 2026-06-15

## Project

`red-team-platform-v5` — Add 5 safeguards-portfolio features to an existing FastAPI + React/TypeScript + PostgreSQL red-teaming platform: stateful case review, audit log, SSE streaming replay, auto-triage layer, and GitHub Actions CI/CD.

## Requirements

1. `POST /runs/{run_id}/review` persists a decision (approve/flag/escalate) to `case_reviews` table; upserts if decision already exists
2. `GET /runs/{run_id}/review` returns the current decision for a run, or 404 if none
3. `GET /audit-log?decision=&reviewer=&limit=50&offset=0` returns paginated audit log entries
4. Every POST to review also appends a row to `audit_log` (append-only)
5. `GET /runs/stream?speed=normal` emits SSE events for all runs in chronological order; supports fast/normal/slow speeds; ends with `event: done`
6. `GET /runs/triage-summary` returns counts per tier: auto_safe / review / auto_flag
7. `GET /runs` accepts `triage_tier` query param and filters accordingly (computed from classifier_score)
8. `RunOut` schema includes `triage_tier` field computed from `classifier_score` at query time
9. CaseReview page shows triage tier summary badges; filter toggles All/Needs Review/Auto-Safe/Auto-Flagged; default = Needs Review
10. CaseReview page shows decision form (3 buttons + reason textarea + submit); shows decision badge if decision exists with Edit option
11. AuditLog page shows paginated table with timestamp, reviewer, run excerpt, decision badge, reason; filter dropdowns for decision type and reviewer
12. Analytics tab has a "Live Feed" collapsible section with Play/Pause, speed selector, scrolling table of last 50 events
13. App.tsx adds "Case Review" tab and "Audit Log" tab (total: 6 tabs, up from 4)
14. `.github/workflows/ci.yml` has backend and frontend parallel jobs; backend job uses postgres service
15. All existing tests continue to pass; `ruff check` and `tsc --noEmit` both pass

## Technology Stack

| Concern | Choice | Reason |
|---------|--------|--------|
| Backend language | Python 3.12 | Existing |
| Backend framework | FastAPI | Existing |
| ORM | SQLAlchemy async + asyncpg | Existing |
| Package manager | uv | Existing |
| Linter/formatter | ruff | Existing |
| Testing | pytest + pytest-asyncio | Existing |
| Frontend language | TypeScript 5.x | Existing |
| Frontend framework | React 18 + Vite | Existing |
| Styling | Tailwind v4 | Existing |
| Data fetching | TanStack Query | Existing |
| SSE | Browser EventSource API (no library) | Brief constraint |
| Frontend testing | vitest + @testing-library/react | Existing |
| CI | GitHub Actions | Feature 5 |

## File and Module Structure

### New/modified backend files
```
src/red_team_platform/
├── models.py                     — add CaseReview + AuditLogEntry ORM models
├── api/
│   ├── schemas.py                — add CaseReviewCreate/Out, AuditLogEntryOut/AuditLogOut; triage_tier on RunOut/SampleOut
│   ├── main.py                   — register review + audit routers
│   └── routers/
│       ├── runs.py               — add SSE stream (BEFORE /{run_id}), triage-summary, triage_tier filter on list
│       ├── review.py             — POST + GET /runs/{run_id}/review [NEW]
│       └── audit.py              — GET /audit-log [NEW]
```

### New/modified frontend files
```
web/src/
├── types/index.ts                — add triage_tier to Run, CaseReview types, AuditLogEntry types
├── hooks/
│   ├── useCaseReview.ts          — query + mutation [NEW]
│   ├── useAuditLog.ts            — query [NEW]
│   └── useTriageSummary.ts       — query [NEW]
├── pages/
│   ├── CaseReview.tsx            — new page replacing SampleReview functionally [NEW]
│   ├── AuditLog.tsx              — new audit log page [NEW]
│   └── Analytics.tsx             — add Live Feed section [MODIFIED]
└── App.tsx                       — add Case Review + Audit Log tabs [MODIFIED]
```

### New CI file
```
.github/workflows/ci.yml          — backend + frontend parallel jobs [NEW]
```

## Open Questions for Architect

None — all structural decisions specified in brief and implementation mission.

## Handoff

Next role: architect
Architect confirms the data model field types, API contract details, component tree, and SSE generator pattern.
