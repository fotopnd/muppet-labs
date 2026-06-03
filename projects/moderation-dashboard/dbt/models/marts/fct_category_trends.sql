-- Event count by hour and category
SELECT
    event_hour,
    category,
    COUNT(*) AS event_count
FROM {{ ref('stg_events') }}
GROUP BY event_hour, category
ORDER BY event_hour DESC, event_count DESC
