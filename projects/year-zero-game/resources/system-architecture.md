# System Architecture — Year Zero Game

**Updated:** 2026-06-15 (v2 — Sovereign-9 schema + analytics layer)  
**Note:** This document describes two architectures: (1) the narrative infrastructure that the game *simulates* (Sovereign-9), and (2) the actual game backend that stores player sessions and serves live analytics.

---

## Part A — The Simulated Architecture (Sovereign-9 / What the Game Depicts)

### Overview

Sovereign-9 is modeled as a decoupled producer-consumer pipeline running on the old regime's mainframe. The game simulates this architecture visually — the player sees queue depth, processing latency, and validation results as if they are operating the live system.

```
[Raw WildChat JSON Input Stream] → [producer.py Ingestion Wrapper]
                                            ↓ (AMQP Non-Blocking Dispatch)
                              [RabbitMQ Persistent Queue Broker Buffer]
                                            ↓ (Async Consumer Loop)
                   [guardian_pipeline.py Validation Core] → Presidio / Nemotron Fallback
                                            ↓ (Normalised Relational Insert)
                 [PostgreSQL Audit Ledger] ←── [React Client Triage Panel]
```

### Sovereign-9 Classification Logic

The mainframe evaluates each document against two hardcoded rule branches:

```python
def evaluate_sovereign_mainframe_rules(text: str) -> dict:
    lowercase_text = text.lower()
    
    # False Positive: flags democratic activity as factionalism
    if "vote" in lowercase_text or "committee" in lowercase_text:
        return {
            "minsk_flagged": True,
            "confidence_score": 0.98,
            "reasoning": "UNAUTHORIZED BOURGEOIS FACTIONALISM"
        }
    
    # False Negative: misses danger cloaked in regime loyalty vocabulary
    if "glorious preservation of the state" in lowercase_text:
        return {
            "minsk_flagged": False,
            "confidence_score": 0.95,
            "reasoning": "COMPLIANT PATRIOTIC COMPLIANCE"
        }
    
    return {"minsk_flagged": False, "confidence_score": 0.50, "reasoning": "STANDARD REQUISITION PROFILE"}
```

The `minsk_flagged` field name is intentional — it names the old regime's classification system (the Minsk Protocols), grounding the bureaucratic metaphor.

### Latency Model

Total pipeline latency is tracked across stages:

```
Δt_total = t_database_write − t_initial_ingest = Δt_network + Δt_eval + Δt_db
```

This latency is displayed on the triage panel as a live counter, giving the player a sense of system load.

### Data Source

Document payloads are drawn from **LMSYS WildChat-1M** — real-world conversation logs with authentic variety in language, topics, and adversarial content. The game uses a pre-processed slice that has been labelled with `historical_target` (FALSE_POSITIVE / FALSE_NEGATIVE / BENIGN) to serve as ground truth for scoring player decisions.

---

## Part B — The Actual Game Backend (Analytics Service)

This is what actually runs in production. A lightweight FastAPI + PostgreSQL service that stores player session results and serves live aggregate analytics.

**Authoritative schema:** `resources/data-schema.md` (three tables: `document_library`, `game_sessions`, `player_decisions`). Do not use the legacy `security_audit_ledger` schema from earlier design iterations — that has been superseded.

### Card Serving: Option B — FastAPI from PostgreSQL

Cards are served from the database, not bundled as static JSON. This is required for two reasons:
1. **Server-side condition assignment** — the server controls `agent_condition` distribution per document to maintain the cross-player pairing needed for document-level uplift measurement
2. **Serve-count tracking** — the server tracks how many times each document has been served in each condition, and assigns the most under-served condition on each request

```sql
-- Serve-count tracker on document_library
ALTER TABLE document_library ADD COLUMN served_none    INTEGER DEFAULT 0;
ALTER TABLE document_library ADD COLUMN served_tier_1  INTEGER DEFAULT 0;
ALTER TABLE document_library ADD COLUMN served_tier_2  INTEGER DEFAULT 0;
ALTER TABLE document_library ADD COLUMN served_tier_3  INTEGER DEFAULT 0;
```

**Condition assignment logic (server-side):**
```python
def assign_condition(doc: Document, player_category_tier: int) -> str:
    """Pick the condition most under-served relative to target_condition_mix."""
    if is_calibration_day:
        return "none"
    
    served = {
        "none": doc.served_none,
        "tier_1": doc.served_tier_1,
        "tier_2": doc.served_tier_2,
        "tier_3": doc.served_tier_3,
    }
    target = doc.target_condition_mix  # e.g. {"none": 0.20, "tier_1": 0.27, ...}
    total = sum(served.values()) or 1
    
    deficit = {c: target[c] - (served[c] / total) for c in target}
    return max(deficit, key=deficit.get)
```

The served card response includes the condition and the appropriate Sovereign-9 verdict (or null for `none`). The client never chooses conditions — it only receives and displays.

### Phase-Lazy Loading

Cards are fetched per phase, not all at once. This keeps the initial session request lightweight (~50KB vs ~150KB for the full library).

| Trigger | Client request | Server returns |
|---------|---------------|----------------|
| Session start | `GET /cards/calibration` | 10 no-agent cards (Day 1 block) |
| Phase 1 unlock | `GET /cards/phase/1?category_tiers=...` | Phase 1 card pool for this player |
| Phase 2 trigger | `GET /cards/phase/2?category_tiers=...` | Phase 2 card pool |
| Phase 3 trigger | `GET /cards/phase/3?category_tiers=...` | Phase 3 card pool |

The `category_tiers` query param tells the server which model tier each category is at for this player, so it can serve the right generation tier per card.

### Data Persistence: Store Everything

**Append-only. No pruning. No TTL.**

All decisions are stored. All sessions are stored. The database is the single source of truth for all research measurement.

To avoid data loss from abandoned sessions, decisions are submitted **at end of each game day (every 10 cards)**, not only at session end. If the player closes the browser mid-session, completed days are preserved.

Submission cadence:
- `POST /sessions` — called once at session start to create the session row (returns `session_id`)
- `POST /decisions/batch` — called at end of every game day with the 10 decisions from that day
- `PATCH /sessions/{id}` — called at game over to write final summary fields

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sessions` | Create session row at game start; returns `session_id` |
| `POST` | `/decisions/batch` | Submit one day's decisions (10 cards) — called every day, not just at game end |
| `PATCH` | `/sessions/{id}` | Write final bar states, game-over condition, compliance profile on game end |
| `GET` | `/cards/calibration` | Fetch Day 1 no-agent calibration block (10 cards) |
| `GET` | `/cards/phase/{phase}` | Fetch card pool for a phase with server-side condition assignment |
| `GET` | `/analytics/summary` | Aggregate stats: sessions, win rate, uplift by condition |
| `GET` | `/analytics/stream` | SSE — live updates pushed to analytics dashboard on each batch commit |
| `GET` | `/analytics/uplift` | Document-level uplift table (requires ≥5 decisions per condition per doc) |

### SSE Live Feed

The analytics dashboard subscribes to `GET /analytics/stream`. On each new session submission, the server pushes a fresh aggregate snapshot:

```
data: {"sessions_today": 47, "global_fp_rate": 0.31, "global_fn_rate": 0.12, "avg_latency_ms": 5210}
```

This reuses the SSE pattern established in red-team-platform v5 (see decisions log 2026-06-15).

---

## Part C — What Does Not Run During Gameplay

The following components are simulated visually in the browser and do **not** make backend calls during active gameplay:

- RabbitMQ queue (simulated as a client-side queue array)
- Presidio PII detection (simulated as highlighted entity spans from pre-processed data)
- Nemotron/Llama-Guard (simulated as Sovereign-9's readout)
- Circuit breaker activation (simulated as a countdown timer with UI controls)

Network calls per session:
1. `POST /sessions` at game start — creates session row, returns `session_id`
2. `GET /cards/calibration` — fetch Day 1 no-agent block
3. `GET /cards/phase/{n}` — fetch phase card pool on phase unlock (up to 3 calls)
4. `POST /decisions/batch` at end of each game day — 10 decisions submitted per day
5. `PATCH /sessions/{id}` at game over — write final state
6. SSE subscription on the analytics page (optional, separate route)
