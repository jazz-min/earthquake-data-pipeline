-- Most Active Regions
SELECT
  place,
  COUNT(*) AS quake_count
FROM {{ ref('stg_earthquakes') }}
GROUP BY place
ORDER BY quake_count DESC
LIMIT 20