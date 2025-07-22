-- Global Earthquake Map
-- Provide all necessary geospatial data
SELECT
  id,
  time,
  place,
  magnitude,
  latitude,
  longitude,
  depth_km
FROM {{ ref('stg_earthquakes') }}
WHERE latitude IS NOT NULL AND longitude IS NOT NULL