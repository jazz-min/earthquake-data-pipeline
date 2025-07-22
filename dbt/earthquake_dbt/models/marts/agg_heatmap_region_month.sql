-- Earthquakes by Region and Month
-- Suitable for heatmap chart

SELECT
  place,
  year_month,
  COUNT(*) AS quake_count
FROM {{ ref('stg_earthquakes') }}
GROUP BY place, year_month
ORDER BY year_month, place