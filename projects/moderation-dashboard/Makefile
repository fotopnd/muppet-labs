.PHONY: producer consumers anomaly escalation api all stop dbt-refresh logs-dir

logs-dir:
	mkdir -p logs

producer:
	uv run md-producer $(ARGS)

consumers: logs-dir
	@echo "Starting production consumers (round-robin group)..."
	uv run md-consumer --model distilbert --mode production > logs/prod-distilbert.log 2>&1 &
	uv run md-consumer --model roberta --mode production > logs/prod-roberta.log 2>&1 &
	uv run md-consumer --model detoxify --mode production > logs/prod-detoxify.log 2>&1 &
	@echo "Starting shadow consumers (per-model groups)..."
	uv run md-consumer --model distilbert --mode shadow > logs/shadow-distilbert.log 2>&1 &
	uv run md-consumer --model roberta --mode shadow > logs/shadow-roberta.log 2>&1 &
	uv run md-consumer --model detoxify --mode shadow > logs/shadow-detoxify.log 2>&1 &
	@echo "Consumers started. Logs in logs/"

anomaly: logs-dir
	uv run md-anomaly > logs/anomaly.log 2>&1 &
	@echo "Anomaly detector started."

escalation: logs-dir
	uv run md-escalation > logs/escalation.log 2>&1 &
	@echo "Escalation service started."

api:
	uv run md-api

dbt-refresh:
	cd dbt && dbt run

all: logs-dir
	uv run md-api &
	sleep 3
	$(MAKE) consumers
	$(MAKE) anomaly
	$(MAKE) escalation
	sleep 5
	uv run md-producer $(ARGS)

stop:
	@pkill -f "moderation_dashboard" 2>/dev/null || true
	@pkill -f "md-" 2>/dev/null || true
	@echo "All moderation-dashboard processes stopped."
