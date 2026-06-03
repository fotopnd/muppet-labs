-- Per-hour F1 score by group and model
SELECT
    classification_hour,
    "group",
    model_name,
    COUNT(*)                                                                        AS n,
    SUM(CASE WHEN predicted_label = 1 AND correct     THEN 1 ELSE 0 END)           AS tp,
    SUM(CASE WHEN predicted_label = 1 AND NOT correct THEN 1 ELSE 0 END)           AS fp,
    SUM(CASE WHEN predicted_label = 0 AND NOT correct THEN 1 ELSE 0 END)           AS fn,
    2.0 * SUM(CASE WHEN predicted_label = 1 AND correct THEN 1 ELSE 0 END)::float
        / NULLIF(
            2 * SUM(CASE WHEN predicted_label = 1 AND correct     THEN 1 ELSE 0 END)
              + SUM(CASE WHEN predicted_label = 1 AND NOT correct THEN 1 ELSE 0 END)
              + SUM(CASE WHEN predicted_label = 0 AND NOT correct THEN 1 ELSE 0 END),
            0
          )                                                                         AS f1
FROM {{ ref('stg_classifications') }}
GROUP BY classification_hour, "group", model_name
ORDER BY classification_hour DESC
