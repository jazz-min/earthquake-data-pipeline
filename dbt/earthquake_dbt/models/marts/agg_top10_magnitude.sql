--- top 10 strongest Earthquakes

SELECT
  id,
  time,
  place,
  longitude,
  latitude,
  magnitude,
  depth_km
FROM {{ ref('stg_earthquakes') }}
ORDER BY magnitude DESC
LIMIT 10