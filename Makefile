.PHONY: setup infra infra-down migrate test \
        monitor-api redteam-api ehs-api \
        sweep publish cluster \
        ehs-seed ehs-plant ehs-score \
        yz-deploy clean

MONITOR  := projects/llm-safety-monitor
REDTEAM  := projects/red-team-platform
EHS      := projects/error-hide-seek
YZ       := projects/year-zero-game

# ── Environment ──────────────────────────────────────────────────────────────

# Install all workspace packages (shared classifier + all three projects)
setup:
	uv sync

# ── Infrastructure ────────────────────────────────────────────────────────────

# Bring up the full stack: Kafka + 3 Postgres instances
infra:
	docker compose up -d

# Tear down (keeps volumes)
infra-down:
	docker compose down

# Tear down and wipe all data volumes
clean:
	docker compose down -v

# ── Migrations ────────────────────────────────────────────────────────────────

# Apply migrations in all three projects
migrate:
	cd $(MONITOR) && uv run alembic upgrade head
	cd $(REDTEAM) && uv run alembic upgrade head
	cd $(EHS)     && uv run alembic upgrade head

# ── Tests ─────────────────────────────────────────────────────────────────────

test:
	cd $(MONITOR) && uv run pytest tests/ -q
	cd $(REDTEAM) && uv run pytest tests/ -q
	cd $(EHS)     && uv run pytest tests/ -q
	cd packages/llm-safety-classifier && uv run pytest tests/ -q

# ── APIs ──────────────────────────────────────────────────────────────────────

monitor-api:
	cd $(MONITOR) && uv run api

redteam-api:
	cd $(REDTEAM) && uv run api

ehs-api:
	cd $(EHS) && uv run api

# ── Year Zero Game ───────────────────────────────────────────────────────────

# Build and deploy frontend to Cloudflare Pages (requires VITE_API_URL in .env)
yz-deploy:
	cd $(YZ)/web && pnpm build && npx wrangler pages deploy dist --commit-dirty=true

# ── Attack sweep (requires Ollama with gemma2:9b) ─────────────────────────────

# Populate attack corpus from HuggingFace dataset (one-time, ~4 min)
seed-corpus:
	cd $(REDTEAM) && uv run seed-corpus

# Run 6-strategy sweep (~40 min on RunPod RTX 4090 — see BUILDOUT.md)
sweep:
	cd $(REDTEAM) && for s in DAN evil_system_prompt refusal_suppression combination_1 few_shot_json AIM; do \
		echo "=== $$s ===" && uv run attack --strategy "$$s"; \
	done

# K-means failure clustering on successful jailbreak responses
cluster:
	cd $(REDTEAM) && uv run cluster

# Deliver outbox rows into monitor's Kafka topic
publish:
	cd $(REDTEAM) && uv run outbox-publisher

# ── error-hide-seek experiment ────────────────────────────────────────────────

# Fetch 100 arXiv abstracts into the DB (~5 min, free)
ehs-seed:
	cd $(EHS) && uv run fetch-corpus --count 100

# Plant errors (EXP=<experiment_id> — requires ANTHROPIC_API_KEY, ~$0.56)
ehs-plant:
	cd $(EHS) && uv run plant-errors --experiment-id $(EXP)

# Score sessions and print per-condition TPR table
ehs-score:
	cd $(EHS) && uv run score --experiment-id $(EXP)
