## Sprint Manifest — gridiron off-season engine Phase 1 — 2026-06-26

**Feature set:** Schema foundation + prospect generation + off-season API stubs
**Total units:** 3 — serial: 01 → 02 → 03

| ID | Slug | Brief | Status | Depends on |
|---|---|---|---|---|
| 01 | offseason-schema | roles/brief/archive/2026-06-26-offseason-schema-brief.md | pending | — |
| 02 | prospect-generation | roles/brief/archive/2026-06-26-prospect-generation-brief.md | pending | 01 |
| 03 | offseason-api-stubs | roles/brief/archive/2026-06-26-offseason-api-stubs-brief.md | pending | 01 |

| Unit | Files owned |
|---|---|
| 01 | `alembic/versions/f7a8b9c0d1e2_offseason_schema.py` |
| 02 | `gridiron/engine/offseason.py` (new, gitignored) |
| 03 | `gridiron/api/routers/offseason.py` (new), `gridiron/api/main.py` |

Review/Retro: combined after all 3 units complete. No deploy.

---

### Ponytail note

Phase 2 (graduation, portal, recruiting, training camp) is deliberately separate — Phase 1 gives us the schema and data-generation primitives to validate the model before writing the sim logic.
