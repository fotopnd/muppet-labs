.PHONY: infra producer consumers api all stop migrate test

infra:
	docker compose up -d

migrate:
	uv run alembic upgrade head

producer:
	uv run producer

consumers:
	uv run consumers

api:
	uv run uvicorn llm_safety_monitor.api.main:app --reload --host 0.0.0.0 --port 8002

all: infra
	@sleep 5
	$(MAKE) migrate
	$(MAKE) producer &
	$(MAKE) consumers &
	$(MAKE) api

stop:
	docker compose down

test:
	uv run pytest tests/ -v
