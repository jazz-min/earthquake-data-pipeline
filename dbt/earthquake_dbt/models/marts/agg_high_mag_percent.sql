--High Magnitude Quake Percent (used for KPI card)

WITH total_quakes AS (
  SELECT COUNT(*) AS total FROM {{ ref('stg_earthquakes') }}
),
high_mag_quakes AS (
  SELECT COUNT(*) AS high_mag FROM {{ ref('stg_earthquakes') }} WHERE magnitude >= 5.0
)
SELECT
  ROUND(high_mag * 100.0 / total, 2) AS high_mag_pct
FROM high_mag_quakes, total_quakes