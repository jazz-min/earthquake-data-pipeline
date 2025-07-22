

SELECT
  ROUND(magnitude::numeric, 1) AS magnitude,
  COUNT(*) AS freq
FROM {{ ref('stg_earthquakes') }}
GROUP BY magnitude
ORDER BY magnitude