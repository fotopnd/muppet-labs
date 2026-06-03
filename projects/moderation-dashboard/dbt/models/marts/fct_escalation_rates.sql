-- Escalation rate per 5-minute window
WITH windowed_events AS (
    SELECT
        date_trunc('minute', created_at)
            - INTERVAL '1 minute' * (EXTRACT(MINUTE FROM created_at)::int % 5) AS window_5min,
        event_id
    FROM {{ source('moderation', 'classifications') }}
),
event_counts AS (
    SELECT window_5min, COUNT(DISTINCT event_id) AS total_events
    FROM windowed_events
    GROUP BY window_5min
),
escalation_counts AS (
    SELECT
        date_trunc('minute', created_at)
            - INTERVAL '1 minute' * (EXTRACT(MINUTE FROM created_at)::int % 5) AS window_5min,
        COUNT(*) AS escalation_count
    FROM {{ source('moderation', 'escalations') }}
    WHERE escalation_reason != 'no_escalation'
    GROUP BY window_5min
)
SELECT
    e.window_5min,
    COALESCE(esc.escalation_count, 0)       AS escalation_count,
    e.total_events,
    COALESCE(esc.escalation_count, 0)::float / NULLIF(e.total_events, 0) AS escalation_rate
FROM event_counts e
LEFT JOIN escalation_counts esc USING (window_5min)
ORDER BY window_5min DESC
