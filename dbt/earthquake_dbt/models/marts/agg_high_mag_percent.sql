with total_quakes as (
  select count(*) as total from {{ ref('stg_earthquakes') }}
),
high_mag_quakes as (
  select count(*) as high_mag from {{ ref('stg_earthquakes') }} where magnitude >= 5.0
)

select
  round(high_mag * 100.0 / total, 2) as high_mag_pct
from high_mag_quakes, total_quakes

