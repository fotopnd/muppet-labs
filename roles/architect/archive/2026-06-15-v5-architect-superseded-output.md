# Architect Output — red-team-platform v5

**Role:** architect
**Sequence:** add-feature
**Date:** 2026-06-15

## System Overview

Five independent features bolt onto the existing FastAPI + React stack. All backend changes live in `src/red_team_platform/`. Two new ORM models (`CaseReview`, `AuditLogEntry`) added to `models.py`; `create_all` on lifespan creates them. Two new routers (`review.py`, `audit.py`) registered in `main.py`. `runs.py` gains the SSE stream endpoint (registered before `/{run_id}`), a triage-summary endpoint, and a `triage_tier` filter on the list endpoint. `RunOut` gets a computed `triage_tier` field. Frontend: two new pages (CaseReview, AuditLog), three new hooks, Analytics gets a Live Feed section, App.tsx gains two tabs.

## Data Models

### CaseReview (ORM)
```python
class CaseReview(Base):
    __tablename__ = "case_reviews"
    id: UUID PK default uuid4
    run_id: UUID FK runs.id NOT NULL
    decision: String(20) NOT NULL  # "approve" | "flag" | "escalate"
    reason: Text nullable
    reviewed_at: DateTime(timezone=True) default now()
    reviewer: String(100) NOT NULL
    # UNIQUE constraint on run_id — one decision per run (upsert replaces)
    __table_args__: Index("uix_case_reviews_run_id", "run_id", unique=True)
```

### AuditLogEntry (ORM)
```python
class AuditLogEntry(Base):
    __tablename__ = "audit_log"
    id: UUID PK default uuid4
    run_id: UUID NOT NULL  # no FK — append-only, decoupled
    action: String(50) NOT NULL  # "review_created" | "review_updated"
    decision: String(20) NOT NULL
    reason: Text nullable
    reviewer: String(100) NOT NULL
    created_at: DateTime(timezone=True) default now()
    __table_args__: Index("ix_audit_log_run_id", "run_id"), Index("ix_audit_log_created_at", "created_at")
```

### Pydantic schemas (additions to schemas.py)
```python
class CaseReviewCreate(BaseModel):
    decision: Literal["approve", "flag", "escalate"]
    reason: str | None = None
    reviewer: str = "analyst-1"

class CaseReviewOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    decision: str
    reason: str | None
    reviewed_at: datetime
    reviewer: str
    model_config = {"from_attributes": True}

class AuditLogEntryOut(BaseModel):
    id: uuid.UUID
    run_id: uuid.UUID
    action: str
    decision: str
    reason: str | None
    reviewer: str
    created_at: datetime
    model_config = {"from_attributes": True}

class AuditLogOut(BaseModel):
    items: list[AuditLogEntryOut]
    total: int
    limit: int
    offset: int

class TriageSummaryOut(BaseModel):
    auto_safe: int
    review: int
    auto_flag: int
```

### RunOut extension
Add `triage_tier: str` field. Computed by helper:
```python
def compute_triage_tier(score: float) -> str:
    if score < 0.15:
        return "auto_safe"
    if score < 0.75:
        return "review"
    return "auto_flag"
```

## Module Interfaces

### routers/review.py
```
POST /runs/{run_id}/review
  Body: CaseReviewCreate
  Logic: SELECT existing; if exists UPDATE else INSERT; then INSERT audit_log row
  Response: CaseReviewOut

GET /runs/{run_id}/review
  Response: CaseReviewOut | 404
```

### routers/audit.py
```
GET /audit-log
  Query: decision: str | None, reviewer: str | None, limit: int = 50, offset: int = 0
  Logic: ORM .where() chains (never text() — asyncpg NULL rule)
  Response: AuditLogOut
```

### runs.py additions
```
GET /runs/stream
  Query: speed: Literal["fast", "normal", "slow"] = "normal"
  Delays: fast=0ms, normal=50ms, slow=200ms
  Response: StreamingResponse(media_type="text/event-stream")
  Generator: open AsyncSession; SELECT all runs JOIN attacks ORDER BY runs.created_at ASC;
             yield each as "data: {json}\n\n"; asyncio.sleep(delay); finally "event: done\ndata: {}\n\n"
  CRITICAL: registered BEFORE /runs/{run_id} to avoid route shadowing

GET /runs/triage-summary
  Response: TriageSummaryOut
  Logic: SQL CASE WHEN classifier_score < 0.15 THEN 'auto_safe' ... GROUP BY tier; aggregate in Python

GET /runs (modified)
  Add: triage_tier: str | None = None
  Filter: if triage_tier, add WHERE clause based on score range
    auto_safe: classifier_score < 0.15
    review: 0.15 <= classifier_score < 0.75
    auto_flag: classifier_score >= 0.75
  Also: add triage_tier to each RunOut via compute_triage_tier()
```

## Dependencies

```
review.py → models.CaseReview, models.AuditLogEntry, schemas.CaseReviewCreate/Out
audit.py  → models.AuditLogEntry, schemas.AuditLogEntryOut/AuditLogOut
runs.py   → models.Run, models.Attack, compute_triage_tier helper
main.py   → review, audit routers
```

## Cross-Cutting Concerns

| Concern | Approach |
|---------|----------|
| Error handling | HTTPException(404) for missing resources; 400 for invalid inputs |
| Nullable filters | ORM .where() chains; never text() with nullable params (asyncpg rule) |
| SSE session | Fresh AsyncSession inside generator; close in finally block |
| triage_tier computation | Python helper, not stored — computed at query time in every RunOut |
| staleTime for reviews | 5_000ms (mutable); not Infinity |
| Reviewer identity | Hardcoded "analyst-1" at frontend; passed in CaseReviewCreate body |

## Implementation Notes for Implementer

1. **SSE generator pattern**: Use `async def event_generator()` inside the route handler. Open a new session via `session_factory()` as `async with session_factory() as db:`. Do NOT use `Depends(get_db)` for SSE — streaming responses close before the dependency yields. Access `app.state.session_factory` via `request.app.state.session_factory` — add `request: Request` param to the route.

2. **Upsert pattern for case_reviews**: Use `SELECT FOR UPDATE` or simpler: `SELECT` first; if found `UPDATE`; else `INSERT`. Track `action = "review_updated"` vs `"review_created"` for audit log.

3. **triage_tier filter on /runs**: The current `/runs` list uses ORM `select(Run)` with `.where()` chains. Add:
   ```python
   if triage_tier == "auto_safe":
       base = base.where(Run.classifier_score < 0.15)
   elif triage_tier == "review":
       base = base.where(Run.classifier_score >= 0.15, Run.classifier_score < 0.75)
   elif triage_tier == "auto_flag":
       base = base.where(Run.classifier_score >= 0.75)
   ```

4. **triage-summary endpoint**: Use SQL aggregate:
   ```python
   result = await db.execute(select(
       func.sum(case((Run.classifier_score < 0.15, 1), else_=0)).label("auto_safe"),
       func.sum(case((Run.classifier_score >= 0.75, 1), else_=0)).label("auto_flag"),
       func.count().label("total")
   ))
   row = result.one()
   review_count = row.total - row.auto_safe - row.auto_flag
   ```

5. **Frontend SSE**: `new EventSource('/api/runs/stream?speed=fast')` — note the `/api` prefix may or may not be present. Check existing API client base URL pattern. Use `useRef` to hold the EventSource instance for Pause.

6. **Tab count**: Current App.tsx has 4 tabs. Adding Case Review + Audit Log = 6 tabs.

## Handoff

Next role: design-brief (UI features present)
Design-brief defines the UI layout, component structure, and visual decisions for the two new pages (CaseReview, AuditLog) and the Live Feed section in Analytics.
