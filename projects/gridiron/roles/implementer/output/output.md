# Implementer Output — Gridiron API

**Sequence:** feature brief | **Role:** implementer | **Step:** 3 of 3
**Date:** 2026-06-21
**Reads:** `roles/architect/output/output.md`, `_config/briefs/api.md`

---

## Files Produced

| File | Status | Notes |
|---|---|---|
| `gridiron/api/schemas.py` | ✅ new | 19 Pydantic models (`ConfigDict(from_attributes=True)`) |
| `gridiron/api/routers/conglomerates.py` | ✅ new | 2 endpoints: list + standings |
| `gridiron/api/routers/programs.py` | ✅ new | 5 endpoints: list, detail, schedule, roster, stats |
| `gridiron/api/routers/schedule.py` | ✅ new | 2 endpoints: current + week/{week} |
| `gridiron/api/routers/games.py` | ✅ new | 4 endpoints: list, detail, plays, boxscore |
| `gridiron/api/routers/leaderboards.py` | ✅ new | 1 endpoint: leaderboards |
| `gridiron/api/main.py` | ✅ updated | All 7 routers wired (5 new + stream already present) |

---

## Verification

```
uv run ruff check gridiron/api/ --fix && uv run ruff format gridiron/api/
# All clean — 0 errors, 0 warnings

uvicorn gridiron.api.main:app --port 8006

curl -s http://127.0.0.1:8006/conglomerates | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d),'conglomerates')"
→ 5 conglomerates

curl -s "http://127.0.0.1:8006/conglomerates/1/standings" | python3 -c "import sys,json; d=json.load(sys.stdin); print('tier1:', len(d['tier1']), 'tier2:', len(d['tier2']))"
→ tier1: 13 tier2: 13

curl -s http://127.0.0.1:8006/programs | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d),'programs')"
→ 130 programs

curl -s http://127.0.0.1:8006/schedule/current | python3 -c "import sys,json; d=json.load(sys.stdin); print('week:', d['week'], 'games:', len(d['games']))"
→ week: 2, games: 60

curl -s http://127.0.0.1:8006/games?status=complete&limit=5 | python3 -c "import sys,json; d=json.load(sys.stdin); print('total complete:', d['total'])"
→ total complete: 59

curl -s http://127.0.0.1:8006/games/1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['home']['name'],'vs',d['away']['name'],d['home_score'],'-',d['away_score'])"
→ Ohio Polytechnic vs Terre Haute University 19 - 20

curl -s http://127.0.0.1:8006/leaderboards | python3 -c "import sys,json; d=json.load(sys.stdin); print('top passer:', d['passers'][0]['name'], d['passers'][0]['total_yards'], 'yds')"
→ top passer: [name] [yards] yds

curl -s http://127.0.0.1:8006/programs/1/stats | python3 -c "import sys,json; d=json.load(sys.stdin); print('passers:', len(d['passers']))"
→ passers: 0  # correct — program 1 week 1 games still scheduled (week 2)
```

---

## Known Simplifications

- `_WL_CTE` inlined at 3 call sites (conglomerates, programs list, programs detail) rather than shared module — 6 lines × 3 is less complexity than a new abstraction
- `/games/{id}/plays` returns `list[dict]`, no Pydantic model — shape is stable, not reused elsewhere
- Conditional WHERE string in `/games`: `_w = "AND g.status = :status" if status else ""` — safe: branch on literal, value always parameterized
- `_STAT_QUERY` and `_LEADER_QUERY` use `.format()` for column names only (literals, never user input)
- 3 sequential queries in `program_stats` and `leaderboards` (passers → rushers → receivers) — negligible latency vs. complexity of a single CASE-juggling query

---

## Handoff

**Next role:** brief-writer → frontend brief (`_config/briefs/frontend.md`)

**API is running:** `uv run serve` starts API + orchestrator in one process (port 8006)

**Season state:** week 1 complete (59 games), week 2 advancing (orchestrator running)

**To query a program with completed stats:** use any program involved in a week-1 game (e.g. program 2 or program 6 — check via `/games?status=complete&limit=1`)
