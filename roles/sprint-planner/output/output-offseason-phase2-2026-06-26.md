## Sprint Manifest — gridiron off-season engine Phase 2 — 2026-06-26

**Feature set:** Graduation, portal, recruiting, training camp
**Total units:** 4 — serial: 04 → 05 → 06 → 07

| ID | Slug | Brief | Status | Depends on |
|---|---|---|---|---|
| 04 | graduation-portal | roles/brief/archive/2026-06-26-graduation-portal-brief.md | pending | Phase 1 complete |
| 05 | recruiting | roles/brief/archive/2026-06-26-recruiting-brief.md | pending | 04 |
| 06 | training-camp | roles/brief/archive/2026-06-26-training-camp-brief.md | pending | 05 |
| 07 | offseason-api-full | roles/brief/archive/2026-06-26-offseason-api-full-brief.md | pending | 04, 05, 06 |

| Unit | Files owned |
|---|---|
| 04 | `alembic/versions/<new>_players_program_nullable.py`, `gridiron/engine/offseason.py` (graduation + portal functions) |
| 05 | `gridiron/engine/offseason.py` (recruiting function + player creation) |
| 06 | `gridiron/engine/offseason.py` (training camp function) |
| 07 | `gridiron/api/routers/offseason.py` (replace stubs) |

Off-season sequence: graduation → portal → recruiting → training camp → season starts

Review/Retro: combined after all 4 units. No deploy.
