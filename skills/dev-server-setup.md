# dev-server-setup.md — Starting the Dev Stack (FastAPI + Vite)

> Load this skill in the implementer role when producing a FastAPI + Vite project.
> Use it to produce a `Makefile` or `dev.sh` that starts the stack correctly.
> The implementer should deliver a working startup script, not just prose instructions.

---

## The Rule

**Always start the API server with `--reload`.**

Without `--reload`, code changes require a manual server restart to take effect. In a session
where backend files are being edited, a stale server produces symptoms that look like code bugs
(wrong responses, missing routes, stale behaviour) but are actually just the process running
old code. This wastes debugging time and produces false bug reports.

If `--reload` causes problems (e.g. import-time side effects), fix those — do not remove `--reload`.

---

## Makefile Target (preferred)

Produce this `Makefile` at the project root (alongside `api/` and `web/`):

```makefile
.PHONY: dev api web db

dev: db
	$(MAKE) -j2 api web

api:
	cd api && uv run uvicorn app.main:app --reload --port 8000

web:
	cd web && pnpm dev

db:
	docker compose up -d
```

Usage:
```bash
make dev     # starts Postgres, API (with --reload), and Vite in parallel
make api     # API only
make web     # frontend only
make db      # Postgres only
```

---

## Manual Commands (if Makefile is not produced)

```bash
# 1. Start Postgres
docker compose up -d

# 2. Start API (MUST include --reload)
cd api && uv run uvicorn app.main:app --reload --port 8000

# 3. Start frontend (new terminal)
cd web && pnpm dev
```

---

## Reviewer Check

When reviewing a FastAPI + Vite project, verify:

- [ ] Startup instructions include `--reload` on the uvicorn command
- [ ] A `Makefile` or `dev.sh` exists at the project root
- [ ] The Makefile/script is committed (not just documented in prose)
