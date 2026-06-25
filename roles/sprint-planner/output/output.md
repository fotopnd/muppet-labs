## Sprint Manifest — gridiron — 2026-06-25

**Feature set:** Coach attributes, staff tab, engine influence on play calling and defensive formation, prestige display
**Total units:** 4
**Parallelism:** 01 → 02 → [03 ∥ 04]

---

### Ponytail report

| Decision | What | Why |
|---|---|---|
| MERGED | Features 1+2 (endpoint + StaffTab) into unit 01 | Same deliverable — endpoint exists only to serve the tab |
| MERGED | Features 3+4+5 (OC/DC engine influence) into unit 03 | All touch same gitignored engine files; one agent, one pass |
| SPLIT | Schema migration as standalone unit 02 | Units 03 and 04 both depend on new columns; migration must land first |
| DEFERRED | "Recruiting influence" mechanic (feature 6 partial) | Engine effect on recruiting is undefined — surface attributes first |
| PARALLEL | Units 03 and 04 after 02 | No shared files: 03 is gitignored engine, 04 is API router + frontend |

---

### Units

| ID | Slug | Brief | Status | Depends on | Parallel-safe with |
|---|---|---|---|---|---|
| 01 | staff-tab | roles/brief/archive/2026-06-25-gridiron-01-staff-tab-brief.md | pending | — | — |
| 02 | coach-attributes-schema | roles/brief/archive/2026-06-25-gridiron-02-coach-attributes-schema-brief.md | pending | 01 | — |
| 03 | engine-coach-influence | roles/brief/archive/2026-06-25-gridiron-03-engine-coach-influence-brief.md | pending | 02 | 04 |
| 04 | prestige-and-stats | roles/brief/archive/2026-06-25-gridiron-04-prestige-and-stats-brief.md | pending | 02 | 03 |

---

### Files owned

| Unit | Files owned |
|---|---|
| 01 | `gridiron/api/routers/programs.py`, `gridiron/api/schemas.py` (ProgramCoach only), `web/src/api/hooks.ts`, `web/src/types.ts`, `web/src/pages/ProgramDetail.tsx` |
| 02 | `alembic/versions/<new>.py`, `gridiron/api/schemas.py` (CoachDetail fields), `gridiron/api/routers/coaches.py` (SELECT update only) |
| 03 | `gridiron/engine/game.py`, `gridiron/engine/play_resolver.py`, `gridiron/engine/constants.py` (all gitignored) |
| 04 | `gridiron/api/routers/coaches.py` (points CTE), `gridiron/api/schemas.py` (CoachSeasonRow), `web/src/types.ts` (CoachSeasonRow), `web/src/pages/CoachPage.tsx`, `web/src/pages/ProgramDetail.tsx` (StaffTab prestige stars) |

---

### Execution guide

**To run a unit:**
> "Run the `add-feature` sequence for this brief: [paste brief path]. Project is gridiron at `/Users/fotopnd/Documents/muppet-labs/projects/gridiron/`. Skip the brief step — the brief is already written. Start at planner."

**Merge order:**
1. Run 01 → merge to main
2. Run 02 → merge to main
3. Spawn 03 + 04 in parallel → merge both to main (either order)

**No deploy to fotopnd.dev — localhost only until further notice.**

**Verification after all units complete:**
```bash
# API
curl http://localhost:8006/programs/1/coaches
# → array with coach_id, first_name, last_name, role, rating, prestige, style, run_tendency

curl http://localhost:8006/coaches/1
# → includes prestige, style, run_tendency; season rows with points_scored/points_allowed

# Frontend (port from pnpm dev output)
# /conference/ATLN/programs/1 → Staff tab shows coaches with prestige stars
# /coaches/1 → header shows ★★★☆☆ prestige, season table has Pts/PA columns

# Sim check (after unit 03)
# Run a game in sim-sandbox; query play_log for a team with run_tendency > 0.6
# RUSH share should be higher than for a team with run_tendency < 0.4
```
