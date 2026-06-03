-- Distinct events from classifications; one row per event_id
SELECT DISTINCT ON (event_id)
    event_id,
    category,
    date_trunc('hour', created_at)  AS event_hour,
    created_at
FROM {{ source('moderation', 'classifications') }}
ORDER BY event_id, created_at
