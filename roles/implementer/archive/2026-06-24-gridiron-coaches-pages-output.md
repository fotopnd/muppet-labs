# Implementer Output — gridiron: Coaches Pages

**Role:** implementer
**Sequence:** add-feature
**Date:** 2026-06-24

---

## Phase

Full-stack — Python backend + TypeScript/React frontend.

---

## Files Produced

| File | Purpose |
|------|---------|
| `gridiron/api/routers/coaches.py` | New router — GET /coaches/{coach_id} with two-CTE SQL |
| `gridiron/api/schemas.py` | Added CoachSeasonRow + CoachDetail Pydantic schemas |
| `gridiron/api/main.py` | Registered coaches router |
| `web/src/types/index.ts` | Added CoachSeasonRow + CoachDetail TypeScript types |
| `web/src/api/hooks.ts` | Added useCoach hook |
| `web/src/pages/CoachPage.tsx` | New page — header card + season history table |
| `web/src/App.tsx` | Added `/coaches/:coachId` route |

---

## Setup Steps Taken

None — project already initialised.

---

## Verification

**Backend:**
- `ruff check` passed clean on all 3 modified Python files
- `GET /coaches/1301` returns 200:
  - seasons: [{season:1, wins:0, losses:1, win_pct:0.0, off_yards:240, pass_yards:149, rush_yards:100, def_yards_allowed:322, sacks:2, interceptions:2, games_played:1}]
- `GET /coaches/9999999` returns 404 `{"detail":"Coach not found"}`

**Frontend:**
- `pnpm build` exits 0 — 91 modules, 0 TS errors

---

## Deviations from Architecture

**Bug fix in SQL:** Initial single-CTE LEFT JOIN play_log approach inflated W-L counts (138 losses for 1 game — each play was counted as a loss). Fixed with two-CTE pattern: `wl` aggregates wins/losses at game level; `play_stats` aggregates yard/sack/INT stats; final SELECT joins by season.

---

## Known Gaps

- No links from program detail pages to coach pages (out of scope per brief)
- `rating` field returned in API but not shown in UI (not requested)

---

## How to Run

```bash
curl http://127.0.0.1:8006/coaches/1301
open http://localhost:5180/coaches/1301
```

---

## Handoff

Next role: reviewer. Read `gridiron/api/routers/coaches.py` and `web/src/pages/CoachPage.tsx` directly.
