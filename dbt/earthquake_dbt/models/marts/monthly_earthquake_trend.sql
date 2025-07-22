-- Monthly Earthquake Trend
-- Year-over-Year trend
SELECT
  EXTRACT(YEAR FROM time) AS year,
  EXTRACT(MONTH FROM time) AS month,
  COUNT(*) AS quake_count,
  year_month
FROM {{ ref('stg_earthquakes') }}
GROUP BY year, month, year_month
ORDER BY 1, 2