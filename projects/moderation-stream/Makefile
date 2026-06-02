.PHONY: producer consumers api all stop logs-dir

logs-dir:
	mkdir -p logs

producer:
	uv run moderation-stream-producer $(ARGS)

consumers: logs-dir
	@echo "Starting Phase 1 consumers in background..."
	uv run moderation-stream-distilbert > logs/distilbert.log 2>&1 &
	uv run moderation-stream-roberta > logs/roberta.log 2>&1 &
	uv run moderation-stream-detoxify > logs/detoxify.log 2>&1 &
	@echo "Consumers started. Logs: logs/distilbert.log, logs/roberta.log, logs/detoxify.log"

api:
	uv run moderation-stream-api

all: logs-dir
	uv run moderation-stream-api &
	sleep 3
	uv run moderation-stream-distilbert > logs/distilbert.log 2>&1 &
	uv run moderation-stream-roberta > logs/roberta.log 2>&1 &
	uv run moderation-stream-detoxify > logs/detoxify.log 2>&1 &
	sleep 5
	uv run moderation-stream-producer $(ARGS)

stop:
	@pkill -f "moderation-stream" 2>/dev/null || true
	@echo "All moderation-stream processes stopped."
