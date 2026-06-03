SELECT
    id,
    event_id,
    "group",
    model_name,
    predicted_label,
    correct,
    latency_ms,
    date_trunc('hour', created_at) AS classification_hour,
    created_at
FROM {{ source('moderation', 'classifications') }}
