--Daily Earthquake Counts
-- Suitable for daily trend line chart

SELECT
  DATE_TRUNC('day', time) AS date,
  COUNT(*) AS quake_count
FROM {{ ref('stg_earthquakes') }}
GROUP BY 1
ORDER BY 1
