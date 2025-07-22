-- Average Depth by Region
-- Bar chart: Avg depth per region

SELECT
  place,
  ROUND(AVG(depth_km)::NUMERIC, 2) AS avg_depth_km
FROM {{ ref('stg_earthquakes') }}
GROUP BY place
ORDER BY avg_depth_km DESC