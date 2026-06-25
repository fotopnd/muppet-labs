# Gridiron

24/7 autonomous college football simulation engine. Fictional universe — 130 programs across 5 corporate broadcast conglomerates, playing a 26-week regular season plus a 32-team postseason tournament. No user interaction. The engine runs continuously, streaming live play-by-play to a public web frontend via SSE.

---

## Stack

| Layer | Tech |
|---|---|
| Backend | Python · FastAPI · SQLAlchemy async · PostgreSQL |
| Frontend | React 19 · TypeScript · Tailwind v4 · Vite |
| Streaming | SSE (in-process asyncio queue, single uvicorn worker) |
| Analytics | dbt-postgres · `analytics` schema in PostgreSQL |
| Deploy | Hetzner CX23 (systemd) · Cloudflare Pages |
| Ports (local) | backend 8006 · DB 5438 · frontend 5177 |

---

## Project Structure

```
gridiron/
├── gridiron/           ← backend package (api/, engine/ [private])
├── web/                ← React/TypeScript frontend
├── analytics/          ← dbt analytics layer
│   ├── models/
│   │   ├── staging/    ← views over raw tables (stg_*)
│   │   ├── intermediate/ ← joins and business logic (int_*)
│   │   └── marts/      ← materialised tables for querying (mart_*)
│   └── dbt_project.yml
├── alembic/            ← DB migrations
└── scripts/            ← seed + sim utilities
```

---

## Running

**Backend**
```bash
uv run serve
```

**Simulation** (runs the weekly slate)
```bash
uv run sim
```

**Analytics** (run from `analytics/`)
```bash
uv run --python 3.12 --with dbt-postgres dbt run --profiles-dir .
uv run --python 3.12 --with dbt-postgres dbt test --profiles-dir .
```

**Lineage docs**
```bash
uv run --python 3.12 --with dbt-postgres dbt docs generate --profiles-dir .
uv run --python 3.12 --with dbt-postgres dbt docs serve --profiles-dir .
```

---

## Analytics Layer

dbt models write to an `analytics` schema in the same PostgreSQL database. Three marts are materialised as tables and re-run after each simulation slate:

| Mart | Contents |
|---|---|
| `mart_program_standings` | W-L, ELO, points for/against, conference rank per season |
| `mart_player_leaderboard` | Season stat totals with position rankings |
| `mart_rivalry_records` | Head-to-head history for all canonical rivalry pairs |

Staging views decode the obfuscated player attribute columns (`alpha/delta/sigma/psi/omega` → `clutch/upside/consistency/leadership/rivalry_dna`) for use in analytical queries.

---

## Engine Privacy

`gridiron/engine/` is excluded from this repository. It contains the simulation constants, play probability distributions, and balance parameters that drive the engine. The API layer, frontend, and analytics are fully shareable.
